#!/usr/bin/env python3
"""
Stage 1: Fetch Sitemap and Populate Database
This script downloads a sitemap.xml file and extracts all URLs into a SQLite database.
"""

import sqlite3
import requests
import yaml
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def load_settings():
    """Load configuration from settings.yaml file."""
    with open('settings.yaml', 'r') as f:
        return yaml.safe_load(f)


def create_database(db_path):
    """
    Create the crawl_ledger database with pages table if it doesn't exist.
    
    Table structure:
    - url: The page URL (PRIMARY KEY)
    - cleaned_text: Extracted text content from the page
    - date_success: Last successful crawl timestamp
    - date_fail: Last failed crawl timestamp
    - fail_count: Number of consecutive failures
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create pages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            url TEXT PRIMARY KEY,
            cleaned_text TEXT,
            date_success TEXT,
            date_fail TEXT,
            fail_count INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    return conn


def fetch_sitemap(sitemap_url, user_agent):
    """
    Download the sitemap.xml file from the given URL.
    Returns the response content if successful, None otherwise.
    """
    headers = {'User-Agent': user_agent}
    
    try:
        print(f"Fetching sitemap from: {sitemap_url}")
        response = requests.get(sitemap_url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise error for bad status codes
        return response.content
    except requests.RequestException as e:
        print(f"Error fetching sitemap: {e}")
        return None


def parse_sitemap(xml_content):
    """
    Parse the sitemap XML and extract all URLs.
    Returns a list of URL strings.
    """
    urls = []
    
    try:
        root = ET.fromstring(xml_content)
        
        # Handle XML namespaces (sitemaps use xmlns)
        # Common namespace for sitemaps
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # Find all <loc> tags which contain URLs
        for url_element in root.findall('.//ns:loc', namespace):
            url = url_element.text.strip()
            if url:
                urls.append(url)
        
        # If no namespace, try without it (for simple sitemaps)
        if not urls:
            for url_element in root.findall('.//loc'):
                url = url_element.text.strip()
                if url:
                    urls.append(url)
                    
    except ET.ParseError as e:
        print(f"Error parsing sitemap XML: {e}")
        return []
    
    return urls


def insert_urls(conn, urls):
    """
    Insert URLs into the database.
    Only adds new URLs, skips existing ones.
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


def main():
    """Main execution function."""
    print("=" * 60)
    print("Stage 1: Fetching Sitemap(s) and Populating Database")
    print("=" * 60)
    
    # Load configuration
    settings = load_settings()
    
    # Support both old format (single sitemap_url) and new format (list of sitemap_urls)
    if 'sitemap_urls' in settings['site']:
        sitemap_urls = settings['site']['sitemap_urls']
    elif 'sitemap_url' in settings['site']:
        # Backward compatibility with old config format
        sitemap_urls = [settings['site']['sitemap_url']]
    else:
        print("✗ No sitemap URLs found in settings.yaml")
        print("Please add 'sitemap_urls' to the 'site' section")
        return
    
    user_agent = settings['site']['user_agent']
    db_path = settings['database']['crawl_ledger']
    
    # Create or connect to database
    conn = create_database(db_path)
    print(f"✓ Database ready: {db_path}")
    
    # Process each sitemap
    total_new = 0
    total_existing = 0
    total_urls = 0
    
    for i, sitemap_url in enumerate(sitemap_urls, 1):
        print(f"\n{'=' * 60}")
        print(f"Processing Sitemap {i}/{len(sitemap_urls)}")
        print(f"{'=' * 60}")
        print(f"URL: {sitemap_url}")
        
        # Fetch the sitemap
        xml_content = fetch_sitemap(sitemap_url, user_agent)
        if not xml_content:
            print("✗ Failed to fetch sitemap. Skipping.")
            continue
        
        print("✓ Sitemap downloaded successfully")
        
        # Parse URLs from sitemap
        urls = parse_sitemap(xml_content)
        print(f"✓ Found {len(urls)} URLs in sitemap")
        
        if not urls:
            print("✗ No URLs found in sitemap. Skipping.")
            continue
        
        # Insert URLs into database
        new_count, existing_count = insert_urls(conn, urls)
        print(f"✓ Added {new_count} new URLs")
        print(f"✓ Skipped {existing_count} existing URLs")
        
        # Update totals
        total_new += new_count
        total_existing += existing_count
        total_urls += len(urls)
        
        # Show some sample URLs from this sitemap
        if new_count > 0:
            print(f"\nSample URLs from this sitemap:")
            for url in urls[:3]:
                print(f"  - {url}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("All Sitemaps Processed!")
    print("=" * 60)
    print(f"Sitemaps processed: {len(sitemap_urls)}")
    print(f"Total URLs found: {total_urls}")
    print(f"New URLs added: {total_new}")
    print(f"Already existing: {total_existing}")
    
    # Show overall database stats
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM pages')
    total_in_db = cursor.fetchone()[0]
    print(f"\nTotal URLs in database: {total_in_db}")
    
    # Close database connection
    conn.close()
    print("\n✓ Done! Database updated successfully.")


if __name__ == '__main__':
    main()
