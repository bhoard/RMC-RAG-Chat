#!/usr/bin/env python3
"""
Utility: Clean Up Orphaned Embeddings
This script removes embeddings for chunks that no longer exist.
"""

import sqlite3
import yaml


def load_settings():
    """Load configuration from settings.yaml file."""
    with open('settings.yaml', 'r') as f:
        return yaml.safe_load(f)


def connect_database(db_path):
    """Connect to a SQLite database."""
    return sqlite3.connect(db_path)


def find_orphaned_embeddings(chunks_conn, embeddings_conn):
    """
    Find embeddings whose chunk_id doesn't exist in chunks table.
    """
    chunks_cursor = chunks_conn.cursor()
    embeddings_cursor = embeddings_conn.cursor()
    
    # Get all valid chunk IDs
    chunks_cursor.execute('SELECT chunk_id FROM chunks')
    valid_chunk_ids = set(row[0] for row in chunks_cursor.fetchall())
    
    # Get all embedding chunk IDs
    embeddings_cursor.execute('SELECT embedding_id, chunk_id FROM embeddings')
    all_embeddings = embeddings_cursor.fetchall()
    
    # Find orphans
    orphaned = []
    for embedding_id, chunk_id in all_embeddings:
        if chunk_id not in valid_chunk_ids:
            orphaned.append((embedding_id, chunk_id))
    
    return orphaned


def delete_orphaned_embeddings(embeddings_conn, orphaned_ids):
    """Delete embeddings by their IDs."""
    cursor = embeddings_conn.cursor()
    
    for embedding_id, chunk_id in orphaned_ids:
        cursor.execute('DELETE FROM embeddings WHERE embedding_id = ?', (embedding_id,))
    
    embeddings_conn.commit()


def main():
    """Main execution function."""
    print("=" * 60)
    print("Clean Up Orphaned Embeddings Utility")
    print("=" * 60)
    
    # Load settings
    settings = load_settings()
    chunks_db_path = settings['database']['chunks']
    embeddings_db_path = settings['database']['embeddings']
    
    # Connect to databases
    chunks_conn = connect_database(chunks_db_path)
    embeddings_conn = connect_database(embeddings_db_path)
    
    print(f"✓ Connected to chunks: {chunks_db_path}")
    print(f"✓ Connected to embeddings: {embeddings_db_path}")
    
    # Find orphaned embeddings
    print("\nScanning for orphaned embeddings...")
    orphaned = find_orphaned_embeddings(chunks_conn, embeddings_conn)
    
    if not orphaned:
        print("✓ No orphaned embeddings found!")
        chunks_conn.close()
        embeddings_conn.close()
        return
    
    print(f"Found {len(orphaned)} orphaned embeddings")
    print("\nThese embeddings reference chunks that no longer exist.")
    print("This can happen if chunks were deleted or re-processed.")
    
    # Show some examples
    print("\nExamples:")
    for embedding_id, chunk_id in orphaned[:5]:
        print(f"  Embedding #{embedding_id} → Missing chunk #{chunk_id}")
    
    # Ask for confirmation
    print("\n" + "=" * 60)
    response = input("Delete these orphaned embeddings? [y/N]: ")
    
    if response.lower() != 'y':
        print("Cancelled.")
        chunks_conn.close()
        embeddings_conn.close()
        return
    
    # Delete orphans
    delete_orphaned_embeddings(embeddings_conn, orphaned)
    print(f"\n✓ Deleted {len(orphaned)} orphaned embeddings")
    
    chunks_conn.close()
    embeddings_conn.close()


if __name__ == '__main__':
    main()
