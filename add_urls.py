#!/usr/bin/env python3
"""
Utility: Add External URLs
This script adds individual URLs to the crawl ledger for processing.
Use this for URLs not in your sitemaps (allied organizations, town sites, etc.)
"""

import sqlite3
import yaml
import sys


def load_settings():
    """Load configuration from settings.yaml file."""
    with open('settings.yaml', 'r') as f:
        return yaml.safe_load(f)


def connect_database(db_path):
    """Connect to the crawl_ledger database."""
    return sqlite3.connect(db_path)


def add_urls(conn, urls):
    """
    Add URLs to the database.
    Only adds new URLs, skips existing ones.
    Returns (new_count, existing_count).
    """
    cursor = conn.cursor()
    new_count = 0
    existing_count = 0
    
    for url in urls:
        try:
            # Try to insert the URL
            cursor.execute(
                'INSERT INTO pages (url) VALUES (?)',
                (url,)
            )
            new_count += 1
        except sqlite3.IntegrityError:
            # URL already exists, skip it
            existing_count += 1
    
    conn.commit()
    return new_count, existing_count


def read_urls_from_file(filename):
    """
    Read URLs from a text file (one URL per line).
    Ignores empty lines and lines starting with #.
    """
    urls = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    urls.append(line)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        return None
    
    return urls


def main():
    """Main execution function."""
    print("=" * 60)
    print("Add External URLs Utility")
    print("=" * 60)
    
    # Check arguments
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python3 add_urls.py <url>                    # Add single URL")
        print("  python3 add_urls.py <url1> <url2> ...        # Add multiple URLs")
        print("  python3 add_urls.py --file urls.txt          # Add URLs from file")
        print("\nExamples:")
        print("  python3 add_urls.py 'https://www.ashlandva.gov/about'")
        print("  python3 add_urls.py 'https://example.com/page1' 'https://example.com/page2'")
        print("  python3 add_urls.py --file external_urls.txt")
        print("\nFile format (one URL per line):")
        print("  https://www.ashlandva.gov/about")
        print("  https://www.ashlandva.gov/services")
        print("  # This is a comment")
        print("  https://partner-site.org/info")
        sys.exit(1)
    
    # Parse arguments
    urls = []
    
    if sys.argv[1] == '--file':
        # Read from file
        if len(sys.argv) < 3:
            print("Error: --file requires a filename")
            sys.exit(1)
        
        filename = sys.argv[2]
        print(f"Reading URLs from: {filename}")
        urls = read_urls_from_file(filename)
        
        if urls is None:
            sys.exit(1)
    else:
        # URLs provided as arguments
        urls = sys.argv[1:]
    
    if not urls:
        print("Error: No URLs provided")
        sys.exit(1)
    
    # Validate URLs
    print(f"\nValidating {len(urls)} URL(s)...")
    invalid_urls = []
    
    for url in urls:
        if not url.startswith(('http://', 'https://')):
            invalid_urls.append(url)
    
    if invalid_urls:
        print("\n⚠️  Warning: These URLs don't start with http:// or https://:")
        for url in invalid_urls:
            print(f"  - {url}")
        
        response = input("\nContinue anyway? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
    
    # Load settings and connect to database
    settings = load_settings()
    db_path = settings['database']['crawl_ledger']
    conn = connect_database(db_path)
    
    print(f"✓ Connected to database: {db_path}")
    
    # Show what will be added
    print(f"\nURLs to add:")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")
    
    # Add URLs
    print(f"\nAdding {len(urls)} URL(s) to database...")
    new_count, existing_count = add_urls(conn, urls)
    
    print(f"\n✓ Added {new_count} new URL(s)")
    
    if existing_count > 0:
        print(f"✓ Skipped {existing_count} URL(s) (already in database)")
    
    print(f"\nThese URLs will be crawled on next 'make stage2'")
    
    conn.close()


if __name__ == '__main__':
    main()
