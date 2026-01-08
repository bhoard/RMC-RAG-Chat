SHELL := /bin/bash

.PHONY: help menu setup stage1 stage2 stage3 stage4 query inspect-urls inspect-db clean stats show-content show-chunks show-embeddings add-url add-urls recrawl cleanup-errors cleanup-orphans

# Default target - show menu
help: menu

menu:
	@echo "================================================"
	@echo "       RAG Pipeline Management Menu"
	@echo "================================================"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make setup          - Install dependencies and prepare environment"
	@echo ""
	@echo "Pipeline Stages:"
	@echo "  make stage1         - Fetch sitemap and populate database"
	@echo "  make stage2         - Crawl pages with Crawl4AI"
	@echo "  make stage3         - Process and chunk content"
	@echo "  make stage4         - Generate embeddings"
	@echo "  make query Q=\"...\" - Ask a question (RAG query)"
	@echo ""
	@echo "Database Inspection:"
	@echo "  make inspect-urls   - Show all URLs in crawl ledger"
	@echo "  make inspect-db     - Open SQLite interactive shell"
	@echo "  make stats          - Show database statistics"
	@echo "  make show-content   - Preview crawled content"
	@echo "  make show-chunks    - Preview chunks"
	@echo "  make show-embeddings - Preview embeddings"
	@echo ""
	@echo "Utilities:"
	@echo "  make add-url URL=<url>     - Add single external URL to crawl"
	@echo "  make add-urls FILE=<file>  - Add URLs from file"
	@echo "  make recrawl URL=<pattern> - Force recrawl of specific URLs"
	@echo "  make cleanup-errors        - Remove and reset error pages (429s, etc.)"
	@echo "  make cleanup-orphans       - Remove orphaned embeddings"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          - Remove all databases and start fresh"
	@echo ""
	@echo "================================================"

# Install all required dependencies
setup:
	@echo "Setting up RAG pipeline environment..."
	@echo ""
	@echo "Checking for system dependencies..."
	@command -v sqlite3 >/dev/null 2>&1 || { echo "⚠️  sqlite3 not found. Please run ./setup.sh first"; exit 1; }
	@echo "✓ SQLite3 available"
	@echo ""
	@echo "Installing Python dependencies..."
	pip3 install --upgrade pip
	pip3 install -r requirements.txt
	@echo ""
	@echo "Installing Playwright browsers..."
	playwright install chromium
	@echo ""
	@echo "✓ Setup complete!"

# Stage 1: Fetch sitemap and populate database
stage1:
	@echo "Running Stage 1: Fetch Sitemap..."
	python3 1_fetch_sitemap.py

# Stage 2: Crawl pages with Crawl4AI
stage2:
	@echo "Running Stage 2: Crawl Pages..."
	python3 2_crawl_pages.py

# Stage 3: Process and chunk content
stage3:
	@echo "Running Stage 3: Process Content..."
	python3 3_process_content.py

# Stage 4: Generate embeddings
stage4:
	@echo "Running Stage 4: Generate Embeddings..."
	python3 4_generate_embeddings.py

# RAG Query - Ask a question
query:
	@if [ -z "$(Q)" ]; then \
		echo "Usage: make query Q=\"Your question here\""; \
	else \
		python3 5_rag_query.py "$(Q)"; \
	fi

# Inspect URLs in the database
inspect-urls:
	@echo "All URLs in crawl_ledger.db:"
	@echo "================================================"
	@sqlite3 crawl_ledger.db "SELECT url FROM pages;"

# Open interactive SQLite shell
inspect-db:
	@sqlite3 crawl_ledger.db

# Show database statistics
stats:
	@echo "Database Statistics:"
	@echo "================================================"
	@echo "Crawl Ledger (crawl_ledger.db):"
	@echo -n "  Total URLs: "
	@sqlite3 crawl_ledger.db "SELECT COUNT(*) FROM pages;"
	@echo -n "  Successfully crawled: "
	@sqlite3 crawl_ledger.db "SELECT COUNT(*) FROM pages WHERE date_success IS NOT NULL;"
	@echo ""
	@if [ -f chunks.db ]; then \
		echo "Chunks Database (chunks.db):"; \
		echo -n "  Total chunks: "; \
		sqlite3 chunks.db "SELECT COUNT(*) FROM chunks;"; \
	fi
	@if [ -f embeddings.db ]; then \
		echo "Embeddings Database (embeddings.db):"; \
		echo -n "  Total embeddings: "; \
		sqlite3 embeddings.db "SELECT COUNT(*) FROM embeddings;"; \
	fi

# Clean up databases and start fresh
clean:
	@echo "⚠️  WARNING: This will DELETE all databases!"
	@read -p "Are you sure you want to continue? [y/N] " ans; \
	if [[ "$$ans" == "y" || "$$ans" == "Y" ]]; then \
		rm -f crawl_ledger.db chunks.db embeddings.db vector_store.db; \
		echo "✓ Databases removed"; \
	else \
		echo "Operation cancelled."; \
	fi

# Preview crawled content
show-content:
	@sqlite3 crawl_ledger.db "SELECT url, substr(cleaned_text, 1, 500) FROM pages WHERE cleaned_text IS NOT NULL LIMIT 3;"

# Utility targets