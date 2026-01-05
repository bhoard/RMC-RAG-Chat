#!/usr/bin/env python3
"""
Utility: Clean Up Error Pages
This script removes content that looks like error pages (429s, short content, etc.)
and resets them for recrawling.
"""

import sqlite3
import yaml


def load_settings():
    """Load configuration from settings.yaml file."""
    with open('settings.yaml', 'r') as f:
        return yaml.safe_load(f)


def connect_database(db_path):
    """Connect to the crawl_ledger database."""
    return sqlite3.connect(db_path)


def find_error_pages(conn):
    """
    Find pages that look like error pages:
    - Content contains "429" or "rate limit" in first 200 chars
    - Content is very short (< 100 chars)
    - Content contains common error messages
    """
    cursor = conn.cursor()
    
    # Get all pages with content
    cursor.execute('''
        SELECT url, cleaned_text 
        FROM pages 
        WHERE cleaned_text IS NOT NULL
    ''')
    
    error_pages = []
    
    for url, text in cursor.fetchall():
        if not text:
            continue
            
        text_start = text[:200].lower()
        
        # Check for rate limiting
        if '429' in text_start or 'rate limit' in text_start or 'too many requests' in text_start:
            error_pages.append((url, 'rate_limited'))
        
        # Check for very short content
        elif len(text.strip()) < 100:
            error_pages.append((url, 'too_short'))
        
        # Check for common error pages
        elif 'access denied' in text_start or 'forbidden' in text_start:
            error_pages.append((url, 'access_denied'))
    
    return error_pages


def clean_error_pages(conn, error_pages):
    """
    Reset error pages for recrawling by:
    - Clearing cleaned_text
    - Clearing date_success
    - Resetting fail_count to 0
    """
    cursor = conn.cursor()
    
    for url, reason in error_pages:
        cursor.execute('''
            UPDATE pages 
            SET cleaned_text = NULL,
                date_success = NULL,
                fail_count = 0,
                date_fail = NULL
            WHERE url = ?
        ''', (url,))
    
    conn.commit()


def main():
    """Main execution function."""
    print("=" * 60)
    print("Clean Up Error Pages Utility")
    print("=" * 60)
    
    # Load settings and connect to database
    settings = load_settings()
    db_path = settings['database']['crawl_ledger']
    conn = connect_database(db_path)
    
    print(f"✓ Connected to database: {db_path}")
    
    # Find error pages
    print("\nScanning for error pages...")
    error_pages = find_error_pages(conn)
    
    if not error_pages:
        print("✓ No error pages found!")
        conn.close()
        return
    
    # Group by reason
    reasons = {}
    for url, reason in error_pages:
        if reason not in reasons:
            reasons[reason] = []
        reasons[reason].append(url)
    
    # Show summary
    print(f"\nFound {len(error_pages)} error pages:")
    for reason, urls in reasons.items():
        print(f"  - {reason}: {len(urls)}")
    
    # Show some examples
    print("\nExamples:")
    for url, reason in error_pages[:5]:
        print(f"  [{reason}] {url}")
    
    # Ask for confirmation
    print("\n" + "=" * 60)
    response = input("Clean these pages and reset for recrawl? [y/N]: ")
    
    if response.lower() != 'y':
        print("Cancelled.")
        conn.close()
        return
    
    # Clean the pages
    clean_error_pages(conn, error_pages)
    print(f"\n✓ Cleaned {len(error_pages)} pages")
    print("These pages will be recrawled on next 'make stage2'")
    
    conn.close()


if __name__ == '__main__':
    main()
