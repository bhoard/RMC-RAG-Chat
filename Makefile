.PHONY: help menu setup stage1 stage2 stage3 stage4 inspect-urls inspect-db clean stats show-content show-chunks show-embeddings recrawl

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
	@echo "  make recrawl URL=<pattern> - Force recrawl of specific URLs"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          - Remove all databases and start fresh"
	@echo ""
	@echo "================================================"

# Install all required dependencies
setup:
	@echo "Setting up RAG pipeline environment..."
	@echo ""
	@echo "Installing Python dependencies..."
	pip3 install --upgrade pip
	pip3 install -r requirements.txt
	@echo ""
	@echo "✓ Setup complete!"
	@echo "Next step: Edit settings.yaml with your sitemap URL"
	@echo "Then run: make stage1"

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

# Inspect URLs in the database
inspect-urls:
	@echo "All URLs in crawl_ledger.db:"
	@echo "================================================"
	@sqlite3 crawl_ledger.db "SELECT url FROM pages;"

# Open interactive SQLite shell
inspect-db:
	@echo "Opening crawl_ledger.db in SQLite shell..."
	@echo "Useful commands:"
	@echo "  .tables          - List all tables"
	@echo "  .schema pages    - Show table structure"
	@echo "  SELECT * FROM pages LIMIT 10; - View sample data"
	@echo "  .quit            - Exit shell"
	@echo ""
	@sqlite3 crawl_ledger.db

# Show database statistics
stats:
	@echo "Database Statistics:"
	@echo "================================================"
	@echo "Crawl Ledger (crawl_ledger.db):"
	@echo "  Total URLs:"
	@sqlite3 crawl_ledger.db "SELECT COUNT(*) FROM pages;"
	@echo "  Successfully crawled:"
	@sqlite3 crawl_ledger.db "SELECT COUNT(*) FROM pages WHERE date_success IS NOT NULL;"
	@echo "  Failed crawls:"
	@sqlite3 crawl_ledger.db "SELECT COUNT(*) FROM pages WHERE fail_count > 0;"
	@echo "  Pending crawls:"
	@sqlite3 crawl_ledger.db "SELECT COUNT(*) FROM pages WHERE date_success IS NULL AND fail_count = 0;"
	@echo ""
	@echo "Chunks Database (chunks.db):"
	@if [ -f chunks.db ]; then \
		echo "  Total chunks:"; \
		sqlite3 chunks.db "SELECT COUNT(*) FROM chunks;"; \
		echo "  Unique pages chunked:"; \
		sqlite3 chunks.db "SELECT COUNT(DISTINCT url) FROM chunks;"; \
		echo "  Average chunks per page:"; \
		sqlite3 chunks.db "SELECT ROUND(AVG(chunk_count), 1) FROM (SELECT COUNT(*) as chunk_count FROM chunks GROUP BY url);"; \
	else \
		echo "  No chunks database yet (run stage3)"; \
	fi
	@echo ""
	@echo "Embeddings Database (embeddings.db):"
	@if [ -f embeddings.db ]; then \
		echo "  Total embeddings:"; \
		sqlite3 embeddings.db "SELECT COUNT(*) FROM embeddings;"; \
		echo "  Model used:"; \
		sqlite3 embeddings.db "SELECT DISTINCT model_name FROM embeddings LIMIT 1;"; \
		echo "  Dimensions:"; \
		sqlite3 embeddings.db "SELECT DISTINCT model_dimension FROM embeddings LIMIT 1;"; \
		echo "  Embedding coverage:"; \
		sqlite3 embeddings.db "SELECT ROUND(CAST(COUNT(*) AS FLOAT) / (SELECT COUNT(*) FROM chunks) * 100, 1) || '%' FROM embeddings;" 2>/dev/null || echo "  (run stage3 first)"; \
	else \
		echo "  No embeddings database yet (run stage4)"; \
	fi

# Preview crawled content
show-content:
	@echo "Sample Crawled Content (first 500 chars):"
	@echo "================================================"
	@sqlite3 crawl_ledger.db "SELECT url, substr(cleaned_text, 1, 500) FROM pages WHERE cleaned_text IS NOT NULL LIMIT 3;"

# Preview chunks
show-chunks:
	@echo "Sample Chunks:"
	@echo "================================================"
	@if [ -f chunks.db ]; then \
		sqlite3 chunks.db "SELECT url, chunk_index, chunk_size, token_count, heading_context, substr(chunk_text, 1, 200) FROM chunks LIMIT 5;"; \
	else \
		echo "No chunks database yet (run stage3)"; \
	fi

# Preview embeddings
show-embeddings:
	@echo "Sample Embeddings:"
	@echo "================================================"
	@if [ -f embeddings.db ]; then \
		sqlite3 embeddings.db "SELECT e.embedding_id, e.chunk_id, e.model_name, e.model_dimension, substr(e.embedding_vector, 1, 100) || '...' as vector_preview FROM embeddings e LIMIT 5;"; \
	else \
		echo "No embeddings database yet (run stage4)"; \
	fi

# Force recrawl specific URLs
recrawl:
	@if [ -z "$(URL)" ]; then \
		echo "Usage: make recrawl URL='<pattern>'"; \
		echo "Examples:"; \
		echo "  make recrawl URL='https://example.com/page'"; \
		echo "  make recrawl URL='/blog/*'"; \
	else \
		python3 recrawl.py "$(URL)"; \
	fi

# Clean up databases and start fresh
clean:
	@echo "⚠️  WARNING: This will DELETE all databases!"
	@echo "Are you sure you want to continue? [y/N] " && read ans && [ ${ans:-N} = y ]
	@rm -f crawl_ledger.db chunks.db vector_store.db
	@echo "✓ Databases removed"
