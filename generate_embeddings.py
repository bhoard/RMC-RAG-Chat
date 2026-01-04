#!/usr/bin/env python3
"""
Stage 4: Generate Embeddings
This script creates vector embeddings for text chunks using sentence-transformers.
"""

import sqlite3
import yaml
import json
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer


def load_settings():
    """Load configuration from settings.yaml file."""
    with open('settings.yaml', 'r') as f:
        return yaml.safe_load(f)


def connect_database(db_path):
    """Connect to a SQLite database."""
    return sqlite3.connect(db_path)


def create_embeddings_table(conn, dimension):
    """
    Create the embeddings table if it doesn't exist.
    
    Table structure:
    - embedding_id: Auto-incrementing primary key
    - chunk_id: Foreign key to chunks table
    - embedding_vector: JSON array of floats (the actual embedding)
    - model_name: Which model generated this embedding
    - model_dimension: Vector dimensions
    - created_at: When this embedding was created
    """
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chunk_id INTEGER NOT NULL UNIQUE,
            embedding_vector TEXT NOT NULL,
            model_name TEXT NOT NULL,
            model_dimension INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Create index on chunk_id for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id 
        ON embeddings(chunk_id)
    ''')
    
    # Create index on model_name for filtering by model
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_embeddings_model 
        ON embeddings(model_name)
    ''')
    
    conn.commit()


def get_chunks_to_embed(chunks_conn, embeddings_conn, batch_size, model_name):
    """
    Get chunks that need embedding, prioritized by:
    1. Never embedded (no entry in embeddings table)
    2. Chunk updated since embedding created (chunk.created_at > embedding.created_at)
    3. Different model was used (model changed in settings)
    
    Returns a list of (chunk_id, chunk_text) tuples up to batch_size.
    """
    chunks_cursor = chunks_conn.cursor()
    embeddings_cursor = embeddings_conn.cursor()
    
    chunks_to_embed = []
    
    # Get all chunks
    chunks_cursor.execute('''
        SELECT chunk_id, chunk_text, created_at 
        FROM chunks 
        ORDER BY chunk_id
    ''')
    
    for chunk_id, chunk_text, chunk_created_at in chunks_cursor.fetchall():
        # Check if embedding exists
        embeddings_cursor.execute('''
            SELECT created_at, model_name 
            FROM embeddings 
            WHERE chunk_id = ?
        ''', (chunk_id,))
        
        result = embeddings_cursor.fetchone()
        
        # Priority 1: Never embedded
        if result is None:
            chunks_to_embed.append((chunk_id, chunk_text, 'never_embedded'))
        else:
            embedding_created_at, embedding_model = result
            
            # Priority 2: Chunk updated since embedding created
            if chunk_created_at > embedding_created_at:
                chunks_to_embed.append((chunk_id, chunk_text, 'chunk_updated'))
            
            # Priority 3: Model changed
            elif embedding_model != model_name:
                chunks_to_embed.append((chunk_id, chunk_text, 'model_changed'))
        
        # Stop if we've reached batch size (unless batch_size is 0)
        if batch_size > 0 and len(chunks_to_embed) >= batch_size:
            break
    
    return chunks_to_embed


def embed_texts(texts, model, processing_batch):
    """
    Generate embeddings for a list of texts.
    Processes in smaller batches for efficiency.
    
    Returns a list of embedding vectors (as numpy arrays).
    """
    embeddings = []
    
    # Process in batches for efficiency
    for i in range(0, len(texts), processing_batch):
        batch = texts[i:i + processing_batch]
        
        # Generate embeddings for this batch
        batch_embeddings = model.encode(batch, show_progress_bar=False)
        
        embeddings.extend(batch_embeddings)
    
    return embeddings


def save_embeddings(conn, chunk_ids, embeddings, model_name, dimension):
    """
    Save embeddings to the database.
    Uses INSERT OR REPLACE to handle updates.
    """
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    for chunk_id, embedding in zip(chunk_ids, embeddings):
        # Convert numpy array to JSON string
        embedding_json = json.dumps(embedding.tolist())
        
        cursor.execute('''
            INSERT OR REPLACE INTO embeddings 
            (chunk_id, embedding_vector, model_name, model_dimension, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (chunk_id, embedding_json, model_name, dimension, now))
    
    conn.commit()


def main():
    """Main execution function."""
    print("=" * 60)
    print("Stage 4: Generating Embeddings")
    print("=" * 60)
    
    # Load configuration
    settings = load_settings()
    chunks_db_path = settings['database']['chunks']
    embeddings_db_path = settings['database']['embeddings']
    model_name = settings['embeddings']['model']
    dimension = settings['embeddings']['dimension']
    batch_size = settings['embeddings']['batch_size']
    processing_batch = settings['embeddings']['processing_batch']
    
    # Connect to databases
    chunks_conn = connect_database(chunks_db_path)
    embeddings_conn = connect_database(embeddings_db_path)
    
    print(f"✓ Connected to chunks database: {chunks_db_path}")
    print(f"✓ Connected to embeddings database: {embeddings_db_path}")
    
    # Create embeddings table if needed
    create_embeddings_table(embeddings_conn, dimension)
    print("✓ Embeddings table ready")
    
    # Get chunks to embed
    print(f"\nFinding chunks to embed...")
    print(f"  - Model: {model_name}")
    print(f"  - Dimensions: {dimension}")
    print(f"  - Batch size: {batch_size if batch_size > 0 else 'unlimited'}")
    print(f"  - Processing batch: {processing_batch}")
    
    chunks_to_process = get_chunks_to_embed(chunks_conn, embeddings_conn, batch_size, model_name)
    
    if not chunks_to_process:
        print("\n✓ No chunks need embedding at this time!")
        chunks_conn.close()
        embeddings_conn.close()
        return
    
    print(f"✓ Found {len(chunks_to_process)} chunks to embed")
    
    # Show breakdown by reason
    reasons = {}
    for _, _, reason in chunks_to_process:
        reasons[reason] = reasons.get(reason, 0) + 1
    
    for reason, count in reasons.items():
        print(f"  - {reason}: {count}")
    
    # Load the embedding model
    print(f"\nLoading embedding model: {model_name}")
    print("  (This may take a moment on first run...)")
    
    try:
        model = SentenceTransformer(model_name)
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        print("\nMake sure you have installed sentence-transformers:")
        print("  pip install sentence-transformers")
        chunks_conn.close()
        embeddings_conn.close()
        return
    
    # Verify model dimension matches settings
    model_dimension = model.get_sentence_embedding_dimension()
    if model_dimension != dimension:
        print(f"\n⚠️  WARNING: Model dimension ({model_dimension}) doesn't match settings ({dimension})")
        print(f"   Update settings.yaml to: dimension: {model_dimension}")
        dimension = model_dimension  # Use actual dimension
    
    # Extract chunk IDs and texts
    chunk_ids = [chunk_id for chunk_id, _, _ in chunks_to_process]
    chunk_texts = [text for _, text, _ in chunks_to_process]
    
    # Generate embeddings
    print(f"\nGenerating embeddings...")
    print("=" * 60)
    
    try:
        embeddings = embed_texts(chunk_texts, model, processing_batch)
        print(f"✓ Generated {len(embeddings)} embeddings")
        
        # Show embedding info
        sample_embedding = embeddings[0]
        print(f"  - Vector dimension: {len(sample_embedding)}")
        print(f"  - Sample values: [{sample_embedding[0]:.4f}, {sample_embedding[1]:.4f}, ...]")
        
    except Exception as e:
        print(f"✗ Failed to generate embeddings: {e}")
        chunks_conn.close()
        embeddings_conn.close()
        return
    
    # Save to database
    print(f"\nSaving embeddings to database...")
    save_embeddings(embeddings_conn, chunk_ids, embeddings, model_name, dimension)
    print("✓ Embeddings saved")
    
    # Cleanup
    chunks_conn.close()
    embeddings_conn.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("Embedding Generation Complete!")
    print("=" * 60)
    print(f"Chunks embedded: {len(chunks_to_process)}")
    print(f"Model used: {model_name}")
    print(f"Dimensions: {dimension}")
    print(f"\nRun 'make stats' to see overall progress")


if __name__ == '__main__':
    main()
