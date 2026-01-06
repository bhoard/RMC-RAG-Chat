#!/usr/bin/env python3
"""
Stage 5: RAG Query System
This script answers questions using retrieved context and Claude.
"""

import sqlite3
import yaml
import json
import sys
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from anthropic import Anthropic
from dotenv import load_dotenv


def load_settings():
    """Load configuration from settings.yaml file."""
    with open('settings.yaml', 'r') as f:
        return yaml.safe_load(f)


def connect_database(db_path):
    """Connect to a SQLite database."""
    return sqlite3.connect(db_path)


def get_api_key(settings):
    """
    Get Claude API key from settings or environment.
    Returns the API key or None if not found.
    """
    # Try environment variable first
    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    # Fall back to settings.yaml
    if not api_key and settings['rag'].get('claude_api_key'):
        api_key = settings['rag']['claude_api_key']
    
    return api_key


def embed_query(query, model):
    """
    Generate embedding for the user's query.
    Returns a numpy array.
    """
    embedding = model.encode([query])[0]
    return embedding


def cosine_similarity(vec1, vec2):
    """
    Calculate cosine similarity between two vectors.
    Returns a float between 0 and 1.
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def search_similar_chunks(query_embedding, chunks_conn, embeddings_conn, top_k, min_similarity):
    """
    Find the most similar chunks to the query.
    Returns a list of (chunk_text, url, similarity_score) tuples.
    """
    embeddings_cursor = embeddings_conn.cursor()
    chunks_cursor = chunks_conn.cursor()
    
    # Get all embeddings
    embeddings_cursor.execute('''
        SELECT chunk_id, embedding_vector 
        FROM embeddings
    ''')
    
    similarities = []
    
    for chunk_id, embedding_json in embeddings_cursor.fetchall():
        # Parse the embedding vector
        chunk_embedding = np.array(json.loads(embedding_json))
        
        # Calculate similarity
        similarity = cosine_similarity(query_embedding, chunk_embedding)
        
        # Only consider chunks above minimum similarity
        if similarity >= min_similarity:
            similarities.append((chunk_id, similarity))
    
    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Get top K chunks
    top_similarities = similarities[:top_k]
    
    # Fetch chunk text and metadata
    results = []
    for chunk_id, similarity in top_similarities:
        chunks_cursor.execute('''
            SELECT chunk_text, url, heading_context
            FROM chunks
            WHERE chunk_id = ?
        ''', (chunk_id,))
        
        result = chunks_cursor.fetchone()
        if result:
            chunk_text, url, heading_context = result
            results.append({
                'text': chunk_text,
                'url': url,
                'heading': heading_context,
                'similarity': similarity
            })
    
    return results


def query_claude(query, context_chunks, settings):
    """
    Send query and context to Claude and get response.
    """
    api_key = get_api_key(settings)
    
    if not api_key:
        raise ValueError(
            "No API key found. Set ANTHROPIC_API_KEY environment variable or "
            "add claude_api_key to settings.yaml"
        )
    
    # Initialize Claude client
    client = Anthropic(api_key=api_key)
    
    # Build context from retrieved chunks
    context_text = "\n\n".join([
        f"Source: {chunk['url']}\n"
        f"Section: {chunk['heading'] or 'N/A'}\n"
        f"Content: {chunk['text']}\n"
        f"(Relevance: {chunk['similarity']:.2%})"
        for chunk in context_chunks
    ])
    
    # Build the full prompt
    system_prompt = settings['rag']['system_prompt']
    
    user_message = f"""Context from RMC websites:

{context_text}

---

Question: {query}

Please answer the question based on the context provided above. If the context doesn't contain enough information to answer fully, say so."""
    
    # Call Claude API
    message = client.messages.create(
        model=settings['rag']['model'],
        max_tokens=settings['rag']['max_tokens'],
        temperature=settings['rag']['temperature'],
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    # Extract response text
    response_text = message.content[0].text
    
    return response_text, context_chunks


def main():
    """Main execution function."""
    # Check for query argument
    if len(sys.argv) < 2:
        print("Usage: python3 5_rag_query.py \"Your question here\"")
        print("\nExample:")
        print('  python3 5_rag_query.py "What are RMC\'s admission requirements?"')
        print("\nOr use: make query Q=\"Your question here\"")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    print("=" * 60)
    print("RMC RAG Query System")
    print("=" * 60)
    print(f"\nQuestion: {query}")
    print()
    
    # Load settings
    settings = load_settings()
    chunks_db_path = settings['database']['chunks']
    embeddings_db_path = settings['database']['embeddings']
    model_name = settings['embeddings']['model']
    top_k = settings['rag']['top_k_chunks']
    min_similarity = settings['rag']['min_similarity']
    
    # Connect to databases
    chunks_conn = connect_database(chunks_db_path)
    embeddings_conn = connect_database(embeddings_db_path)
    
    # Load embedding model
    print("Loading embedding model...")
    model = SentenceTransformer(model_name)
    
    # Embed the query
    print("Embedding your question...")
    query_embedding = embed_query(query, model)
    
    # Search for similar chunks
    print(f"Searching for relevant content (top {top_k})...")
    similar_chunks = search_similar_chunks(
        query_embedding, chunks_conn, embeddings_conn, top_k, min_similarity
    )
    
    if not similar_chunks:
        print("\n✗ No relevant content found in the knowledge base.")
        print("Try rephrasing your question or check if the content has been crawled.")
        chunks_conn.close()
        embeddings_conn.close()
        return
    
    print(f"✓ Found {len(similar_chunks)} relevant chunks")
    
    # Show retrieved context
    print("\n" + "-" * 60)
    print("Retrieved Context:")
    print("-" * 60)
    for i, chunk in enumerate(similar_chunks, 1):
        print(f"\n[{i}] {chunk['url']}")
        if chunk['heading']:
            print(f"    Section: {chunk['heading']}")
        print(f"    Relevance: {chunk['similarity']:.1%}")
        preview = chunk['text'][:150].replace('\n', ' ')
        print(f"    Preview: {preview}...")
    
    # Query Claude
    print("\n" + "=" * 60)
    print("Generating answer with Claude...")
    print("=" * 60)
    
    try:
        answer, sources = query_claude(query, similar_chunks, settings)
        
        print("\nAnswer:")
        print("-" * 60)
        print(answer)
        print()
        
        print("\nSources:")
        print("-" * 60)
        unique_urls = list(set(chunk['url'] for chunk in sources))
        for url in unique_urls:
            print(f"  - {url}")
        
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        print("\nTo set up your API key:")
        print("  1. Get a key from: https://console.anthropic.com/")
        print("  2. Set environment variable: export ANTHROPIC_API_KEY='your-key'")
        print("  3. Or add to settings.yaml under rag.claude_api_key")
    
    except Exception as e:
        print(f"\n✗ Error querying Claude: {e}")
    
    # Cleanup
    chunks_conn.close()
    embeddings_conn.close()


if __name__ == '__main__':
    main()
