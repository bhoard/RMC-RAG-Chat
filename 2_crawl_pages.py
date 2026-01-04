#!/usr/bin/env python3
"""
Stage 2: Crawl Pages with Crawl4AI
This script fetches content from URLs in the database and stores cleaned markdown text.
"""

import sqlite3
import yaml
import time
import asyncio
from datetime import datetime, timedelta
from fnmatch import fnmatch
from crawl4ai import AsyncWebCrawler


def load_settings():
    """Load configuration from settings.yaml file."""
    with open('settings.yaml', 'r') as f:
        return yaml.safe_load(f)


def connect_database(db_path):
    """Connect to the crawl_ledger database."""
    return sqlite3.connect(db_path)


def should_ignore_url(url, ignore_patterns):
    """
    Check if a URL matches any of the ignore patterns.
    
    Patterns support wildcards:
    - "/admin/*" matches any URL with /admin/ in the path
    - "*/print/*" matches any URL with /print/ in the path
    - "/login" matches exact path
    
    Returns True if URL should be ignored.
    """
    for pattern in ignore_patterns:
        # Simple wildcard matching
        if fnmatch(url, f"*{pattern}*"):
            return True
    return False


def get_urls_to_crawl(conn, batch_size, recrawl_days, ignore_patterns):
    """
    Get a list of URLs that need to be crawled, prioritized by:
    1. Never crawled (date_success is NULL and fail_count = 0)
    2. Failed previously (fail_count > 0)
    3. Stale (last crawled more than recrawl_days ago)
    
    Returns a list of URLs up to batch_size (or all if batch_size is 0).
    """
    cursor = conn.cursor()
    urls_to_crawl = []
    
    # Calculate the date threshold for recrawling
    recrawl_threshold = (datetime.now() - timedelta(days=recrawl_days)).isoformat()
    
    # Priority 1: Never crawled pages
    cursor.execute('''
        SELECT url FROM pages 
        WHERE date_success IS NULL 
        AND fail_count = 0
        ORDER BY url
    ''')
    never_crawled = [row[0] for row in cursor.fetchall()]
    
    # Priority 2: Failed pages (to retry)
    cursor.execute('''
        SELECT url FROM pages 
        WHERE fail_count > 0
        ORDER BY fail_count ASC, date_fail ASC
    ''')
    failed_pages = [row[0] for row in cursor.fetchall()]
    
    # Priority 3: Stale pages (successful but old)
    cursor.execute('''
        SELECT url FROM pages 
        WHERE date_success IS NOT NULL 
        AND date_success < ?
        ORDER BY date_success ASC
    ''', (recrawl_threshold,))
    stale_pages = [row[0] for row in cursor.fetchall()]
    
    # Combine lists in priority order, filtering out ignored URLs
    all_candidates = never_crawled + failed_pages + stale_pages
    
    for url in all_candidates:
        # Skip ignored URLs
        if should_ignore_url(url, ignore_patterns):
            continue
            
        # Skip duplicates (in case a URL appears in multiple categories)
        if url in urls_to_crawl:
            continue
            
        urls_to_crawl.append(url)
        
        # Stop if we've reached batch size (unless batch_size is 0)
        if batch_size > 0 and len(urls_to_crawl) >= batch_size:
            break
    
    return urls_to_crawl


async def crawl_url(url, crawler):
    """
    Crawl a single URL and return cleaned markdown content.
    
    Returns:
        (success: bool, content: str or None, error: str or None)
    """
    try:
        # Run the crawler on this URL
        result = await crawler.arun(url=url)
        
        # Check if crawl was successful
        if result.success and result.markdown:
            return True, result.markdown, None
        else:
            error_msg = "No content extracted or crawl failed"
            return False, None, error_msg
            
    except Exception as e:
        # Catch any errors during crawling
        error_msg = str(e)
        return False, None, error_msg


def update_success(conn, url, cleaned_text):
    """
    Update database after successful crawl.
    Sets cleaned_text, date_success, and resets fail_count.
    """
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute('''
        UPDATE pages 
        SET cleaned_text = ?,
            date_success = ?,
            fail_count = 0,
            date_fail = NULL
        WHERE url = ?
    ''', (cleaned_text, now, url))
    
    conn.commit()


def update_failure(conn, url, error_msg):
    """
    Update database after failed crawl.
    Increments fail_count and sets date_fail.
    """
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute('''
        UPDATE pages 
        SET fail_count = fail_count + 1,
            date_fail = ?
        WHERE url = ?
    ''', (now, url))
    
    conn.commit()


async def crawl_all_urls(urls, conn, delay):
    """
    Crawl all URLs using async crawler.
    This function coordinates the crawling process.
    """
    success_count = 0
    fail_count = 0
    
    # Create the async crawler
    async with AsyncWebCrawler(verbose=False) as crawler:
        print("✓ Crawler ready")
        print(f"\nStarting crawl (delay: {delay}s between requests)...")
        print("=" * 60)
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Crawling: {url}")
            
            # Crawl the URL
            success, content, error = await crawl_url(url, crawler)
            
            if success:
                # Store the cleaned markdown content
                update_success(conn, url, content)
                success_count += 1
                
                # Show preview of content
                preview = content[:100].replace('\n', ' ')
                print(f"  ✓ Success! ({len(content)} chars)")
                print(f"  Preview: {preview}...")
            else:
                # Record the failure
                update_failure(conn, url, error)
                fail_count += 1
                print(f"  ✗ Failed: {error}")
            
            # Be polite - wait between requests (except for last URL)
            if i < len(urls):
                await asyncio.sleep(delay)
    
    return success_count, fail_count


def main():
    """Main execution function."""
    print("=" * 60)
    print("Stage 2: Crawling Pages with Crawl4AI")
    print("=" * 60)
    
    # Load configuration
    settings = load_settings()
    db_path = settings['database']['crawl_ledger']
    batch_size = settings['crawler']['batch_size']
    recrawl_days = settings['crawler']['recrawl_after_days']
    delay = settings['crawler']['delay_between_requests']
    ignore_patterns = settings['crawler']['ignore_patterns']
    
    # Connect to database
    conn = connect_database(db_path)
    print(f"✓ Connected to database: {db_path}")
    
    # Get URLs to crawl
    print(f"\nFinding URLs to crawl...")
    print(f"  - Batch size: {batch_size if batch_size > 0 else 'unlimited'}")
    print(f"  - Recrawl after: {recrawl_days} days")
    print(f"  - Ignore patterns: {len(ignore_patterns)}")
    
    urls_to_crawl = get_urls_to_crawl(conn, batch_size, recrawl_days, ignore_patterns)
    
    if not urls_to_crawl:
        print("\n✓ No URLs need crawling at this time!")
        conn.close()
        return
    
    print(f"✓ Found {len(urls_to_crawl)} URLs to crawl")
    
    # Initialize and run crawler (async)
    print("\nInitializing Crawl4AI crawler...")
    success_count, fail_count = asyncio.run(crawl_all_urls(urls_to_crawl, conn, delay))
    
    # Cleanup
    conn.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("Crawl Complete!")
    print("=" * 60)
    print(f"Successfully crawled: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"\nRun 'make stats' to see overall progress")


if __name__ == '__main__':
    main()
