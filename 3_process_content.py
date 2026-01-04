#!/usr/bin/env python3
"""
Stage 3: Process and Chunk Content
This script takes cleaned markdown from the crawl ledger and creates chunks for RAG.
"""

import sqlite3
import yaml
import re
from datetime import datetime


def load_settings():
    """Load configuration from settings.yaml file."""
    with open('settings.yaml', 'r') as f:
        return yaml.safe_load(f)


def connect_database(db_path):
    """Connect to a SQLite database."""
    return sqlite3.connect(db_path)


def create_chunks_table(conn):
    """
    Create the chunks table if it doesn't exist.
    
    Table structure:
    - chunk_id: Auto-incrementing primary key
    - url: Source URL (where this chunk came from)
    - chunk_index: Position in the document (0, 1, 2...)
    - chunk_text: The actual chunk content
    - chunk_size: Length of chunk in characters
    - token_count: Approximate token count (chars / 4)
    - heading_context: Markdown heading this chunk falls under
    - created_at: When this chunk was created
    """
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            chunk_size INTEGER NOT NULL,
            token_count INTEGER NOT NULL,
            heading_context TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(url, chunk_index)
        )
    ''')
    
    # Create index on URL for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_chunks_url 
        ON chunks(url)
    ''')
    
    conn.commit()


def extract_heading_context(text, position):
    """
    Find the most recent markdown heading before the given position.
    Returns the heading text (without the # symbols).
    """
    # Find all headings up to this position
    heading_pattern = r'^(#{1,6})\s+(.+)$'
    
    # Look at text before the position
    text_before = text[:position]
    headings = []
    
    for match in re.finditer(heading_pattern, text_before, re.MULTILINE):
        level = len(match.group(1))  # Number of # symbols
        heading_text = match.group(2).strip()
        headings.append((level, heading_text))
    
    # Return the most recent heading, or None
    if headings:
        return headings[-1][1]  # Return just the text
    return None


def split_into_sentences(text):
    """
    Split text into sentences.
    Simple sentence splitter that handles common cases.
    """
    # Split on periods, question marks, exclamation points followed by space
    # But not on common abbreviations
    sentence_endings = re.compile(r'([.!?])\s+(?=[A-Z])')
    sentences = sentence_endings.split(text)
    
    # Rejoin the punctuation with the sentences
    result = []
    for i in range(0, len(sentences) - 1, 2):
        result.append(sentences[i] + sentences[i + 1])
    
    # Add last sentence if exists
    if len(sentences) % 2 == 1:
        result.append(sentences[-1])
    
    return [s.strip() for s in result if s.strip()]


def chunk_text(text, chunk_size, overlap, min_size, respect_sentences, respect_paragraphs):
    """
    Split text into chunks with specified size and overlap.
    
    Returns a list of (chunk_text, start_position) tuples.
    The start_position helps us find the heading context.
    """
    chunks = []
    
    if not text or len(text) < min_size:
        return chunks
    
    # If respecting paragraphs, split on double newlines first
    if respect_paragraphs:
        paragraphs = text.split('\n\n')
        current_chunk = ""
        current_position = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                # Save current chunk
                chunks.append((current_chunk.strip(), current_position))
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + paragraph
                current_position = current_position + len(current_chunk) - len(overlap_text) - len(paragraph)
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                    current_position = text.find(paragraph)
        
        # Add final chunk
        if current_chunk and len(current_chunk) >= min_size:
            chunks.append((current_chunk.strip(), current_position))
    
    # If respecting sentences but not paragraphs
    elif respect_sentences:
        sentences = split_into_sentences(text)
        current_chunk = ""
        current_position = 0
        
        for sentence in sentences:
            # If adding this sentence exceeds chunk size
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                # Save current chunk
                chunks.append((current_chunk.strip(), current_position))
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
                current_position = current_position + len(current_chunk) - len(overlap_text) - len(sentence)
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                    current_position = text.find(sentence)
        
        # Add final chunk
        if current_chunk and len(current_chunk) >= min_size:
            chunks.append((current_chunk.strip(), current_position))
    
    # Simple character-based chunking (fallback)
    else:
        position = 0
        while position < len(text):
            end = position + chunk_size
            chunk = text[position:end]
            
            if len(chunk) >= min_size:
                chunks.append((chunk.strip(), position))
            
            position = end - overlap
    
    return chunks


def estimate_tokens(text):
    """
    Rough estimate of token count.
    Rule of thumb: 1 token ≈ 4 characters for English text.
    """
    return len(text) // 4


def process_page(url, text, chunk_size, overlap, min_size, respect_sentences, respect_paragraphs):
    """
    Process a single page's text into chunks.
    
    Returns a list of chunk dictionaries with metadata.
    """
    chunk_list = chunk_text(text, chunk_size, overlap, min_size, respect_sentences, respect_paragraphs)
    
    processed_chunks = []
    now = datetime.now().isoformat()
    
    for index, (chunk_content, position) in enumerate(chunk_list):
        # Extract heading context for this chunk
        heading = extract_heading_context(text, position)
        
        # Calculate metadata
        size = len(chunk_content)
        tokens = estimate_tokens(chunk_content)
        
        chunk_data = {
            'url': url,
            'chunk_index': index,
            'chunk_text': chunk_content,
            'chunk_size': size,
            'token_count': tokens,
            'heading_context': heading,
            'created_at': now
        }
        
        processed_chunks.append(chunk_data)
    
    return processed_chunks


def insert_chunks(conn, chunks):
    """
    Insert chunks into the database.
    Uses INSERT OR REPLACE to handle updates.
    """
    cursor = conn.cursor()
    
    for chunk in chunks:
        cursor.execute('''
            INSERT OR REPLACE INTO chunks 
            (url, chunk_index, chunk_text, chunk_size, token_count, heading_context, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            chunk['url'],
            chunk['chunk_index'],
            chunk['chunk_text'],
            chunk['chunk_size'],
            chunk['token_count'],
            chunk['heading_context'],
            chunk['created_at']
        ))
    
    conn.commit()


def get_pages_to_process(crawl_conn, chunks_conn):
    """
    Get pages that need processing.
    Returns pages that have been successfully crawled but not yet chunked,
    or pages that have been re-crawled since their chunks were created.
    """
    cursor = crawl_conn.cursor()
    
    # Get all successfully crawled pages
    cursor.execute('''
        SELECT url, cleaned_text, date_success 
        FROM pages 
        WHERE cleaned_text IS NOT NULL 
        AND date_success IS NOT NULL
        ORDER BY date_success DESC
    ''')
    
    pages_to_process = []
    
    for url, text, date_success in cursor.fetchall():
        # Check if chunks exist for this URL
        chunks_cursor = chunks_conn.cursor()
        chunks_cursor.execute('''
            SELECT created_at 
            FROM chunks 
            WHERE url = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (url,))
        
        result = chunks_cursor.fetchone()
        
        # Process if no chunks exist OR crawl is newer than chunks
        if result is None or date_success > result[0]:
            pages_to_process.append((url, text))
    
    return pages_to_process


def main():
    """Main execution function."""
    print("=" * 60)
    print("Stage 3: Processing and Chunking Content")
    print("=" * 60)
    
    # Load configuration
    settings = load_settings()
    crawl_db_path = settings['database']['crawl_ledger']
    chunks_db_path = settings['database']['chunks']
    chunk_size = settings['processing']['chunk_size']
    overlap = settings['processing']['chunk_overlap']
    min_size = settings['processing']['min_chunk_size']
    respect_sentences = settings['processing']['respect_sentences']
    respect_paragraphs = settings['processing']['respect_paragraphs']
    
    # Connect to databases
    crawl_conn = connect_database(crawl_db_path)
    chunks_conn = connect_database(chunks_db_path)
    
    print(f"✓ Connected to crawl ledger: {crawl_db_path}")
    print(f"✓ Connected to chunks database: {chunks_db_path}")
    
    # Create chunks table if needed
    create_chunks_table(chunks_conn)
    print("✓ Chunks table ready")
    
    # Get pages to process
    print("\nFinding pages to process...")
    print(f"  - Target chunk size: {chunk_size} characters")
    print(f"  - Chunk overlap: {overlap} characters")
    print(f"  - Minimum chunk size: {min_size} characters")
    print(f"  - Respect sentences: {respect_sentences}")
    print(f"  - Respect paragraphs: {respect_paragraphs}")
    
    pages = get_pages_to_process(crawl_conn, chunks_conn)
    
    if not pages:
        print("\n✓ No pages need processing at this time!")
        crawl_conn.close()
        chunks_conn.close()
        return
    
    print(f"✓ Found {len(pages)} pages to process")
    
    # Process each page
    print("\nProcessing pages...")
    print("=" * 60)
    
    total_chunks = 0
    
    for i, (url, text) in enumerate(pages, 1):
        print(f"\n[{i}/{len(pages)}] Processing: {url}")
        print(f"  Content length: {len(text)} characters")
        
        # Chunk the text
        chunks = process_page(url, text, chunk_size, overlap, min_size, 
                            respect_sentences, respect_paragraphs)
        
        # Insert into database
        insert_chunks(chunks_conn, chunks)
        
        total_chunks += len(chunks)
        print(f"  ✓ Created {len(chunks)} chunks")
        
        # Show sample chunk
        if chunks:
            sample = chunks[0]['chunk_text'][:100].replace('\n', ' ')
            print(f"  Sample: {sample}...")
    
    # Cleanup
    crawl_conn.close()
    chunks_conn.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("Processing Complete!")
    print("=" * 60)
    print(f"Pages processed: {len(pages)}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Average chunks per page: {total_chunks / len(pages):.1f}")
    print(f"\nChunks stored in: {chunks_db_path}")


if __name__ == '__main__':
    main()
