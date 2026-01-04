#!/usr/bin/env python3
"""
Utility: Force Recrawl Specific URLs
This script allows you to manually mark URLs for recrawling.
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


def mark_for_recrawl(conn, url_pattern):
    """
    Mark URLs for recrawling by clearing their date_success.
    
    Supports:
    - Exact URL: "https://example.com/page"
    - Path pattern: "/blog/*" (matches all URLs with /blog/ in path)
    """
    cursor = conn.cursor()
    
    if '*' in url_pattern:
        # Wildcard pattern - use LIKE
        like_pattern = url_pattern.replace('*', '%')
        cursor.execute('''
            UPDATE pages 
            SET date_success = NULL, fail_count = 0
            WHERE url LIKE ?
        ''', (like_pattern,))
    else:
        # Exact URL match
        cursor.execute('''
            UPDATE pages 
            SET date_success = NULL, fail_count = 0
            WHERE url = ?
        ''', (url_pattern,))
    
    rows_affected = cursor.rowcount
    conn.commit()
    
    return rows_affected


def main():
    """Main execution function."""
    # Check if URL pattern provided
    if len(sys.argv) < 2:
        print("Usage: python3 recrawl.py <url_or_pattern>")
        print("\nExamples:")
        print("  python3 recrawl.py 'https://example.com/page'")
        print("  python3 recrawl.py '/blog/*'")
        print("  python3 recrawl.py '*/2024/*'")
        sys.exit(1)
    
    url_pattern = sys.argv[1]
    
    print("=" * 60)
    print("Force Recrawl Utility")
    print("=" * 60)
    print(f"Pattern: {url_pattern}")
    
    # Load settings and connect to database
    settings = load_settings()
    db_path = settings['database']['crawl_ledger']
    conn = connect_database(db_path)
    
    # Mark URLs for recrawl
    count = mark_for_recrawl(conn, url_pattern)
    
    if count == 0:
        print(f"\n✗ No URLs matched pattern: {url_pattern}")
    else:
        print(f"\n✓ Marked {count} URL(s) for recrawl")
        print("\nRun 'make stage2' to recrawl these URLs")
    
    conn.close()


if __name__ == '__main__':
    main()

