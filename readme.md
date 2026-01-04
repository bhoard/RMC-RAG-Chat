# Simple RAG Pipeline

A straightforward, easy-to-understand RAG (Retrieval-Augmented Generation) pipeline built with Python and SQLite. Perfect for learning or deploying on a small VPS.

## 🎯 Project Goals

- **Simple & Educational**: Written with junior developers in mind
- **Resource Efficient**: Runs on modest hardware (tested on 4-core i5, 16GB RAM)
- **Self-Contained**: Uses SQLite (no external database servers needed)
- **Transparent**: Each pipeline stage is a separate, well-commented script

## 📋 Requirements

- Ubuntu 24.04 LTS (or similar Linux distribution)
- Python 3.10+
- 4GB+ RAM (16GB recommended)
- 20GB+ storage (100GB recommended for larger sites)

## 🚀 Quick Start

### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/simple-rag-pipeline.git
cd simple-rag-pipeline

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
make setup
```

### 2. Configure Your Site

Edit `settings.yaml` and update the sitemap URL:

```yaml
site:
  sitemap_url: "https://your-site.com/sitemap.xml"
```

### 3. Run the Pipeline

```bash
# Fetch URLs from sitemap
make stage1

# Check what was found
make stats
```

## 📁 Project Structure

```
simple-rag-pipeline/
├── README.md                 # This file
├── LICENSE                   # MIT License
├── CONTRIBUTING.md           # Contribution guidelines
├── settings.yaml             # Configuration file
├── Makefile                  # Pipeline management commands
├── requirements.txt          # Python dependencies
├── 1_fetch_sitemap.py       # Stage 1: Fetch URLs from sitemap
├── 2_crawl_pages.py         # Stage 2: Crawl and extract content
├── recrawl.py               # Utility: Force recrawl URLs
├── 3_process_content.py     # Stage 3: Chunk and process text
├── 4_generate_embeddings.py # Stage 4: Create vector embeddings (coming soon)
├── crawl_ledger.db          # SQLite: URLs and raw content
├── chunks.db                # SQLite: Processed chunks
└── vector_store.db          # SQLite: Vector embeddings (coming soon)
```

## 🔧 Available Commands

Run `make` or `make menu` to see all available commands:

- `make setup` - Install dependencies
- `make stage1` - Fetch sitemap URLs
- `make stage2` - Crawl pages with Crawl4AI
- `make stage3` - Process content
- `make stage4` - Generate embeddings (coming soon)
- `make stats` - Show database statistics
- `make show-content` - Preview crawled content
- `make show-chunks` - Preview chunks
- `make inspect-db` - Open SQLite shell
- `make recrawl URL='<pattern>'` - Force recrawl specific URLs
- `make clean` - Remove all databases

## 🗄️ Database Schema

### crawl_ledger.db

**pages table**:
- `url` (TEXT, PRIMARY KEY) - The page URL
- `cleaned_text` (TEXT) - Extracted and cleaned markdown content
- `date_success` (TEXT) - Last successful crawl timestamp
- `date_fail` (TEXT) - Last failed crawl timestamp
- `fail_count` (INTEGER) - Number of consecutive failures

### chunks.db

**chunks table**:
- `chunk_id` (INTEGER, PRIMARY KEY) - Auto-incrementing ID
- `url` (TEXT) - Source URL
- `chunk_index` (INTEGER) - Position in document (0, 1, 2...)
- `chunk_text` (TEXT) - The chunk content
- `chunk_size` (INTEGER) - Length in characters
- `token_count` (INTEGER) - Approximate token count
- `heading_context` (TEXT) - Markdown heading this chunk falls under
- `created_at` (TEXT) - When chunk was created

## 🛠️ Pipeline Stages

### Stage 1: Fetch Sitemap ✅
Fetches your sitemap.xml and extracts all URLs into the database.

```bash
make stage1
```

### Stage 2: Crawl Pages ✅
Uses Crawl4AI to fetch and clean content from each URL. Stores markdown content in database.

Features:
- Configurable batch sizes
- Smart prioritization (never crawled → failed → stale)
- URL ignore patterns
- Automatic retry logic
- Periodic recrawling

```bash
# Crawl pages (uses batch_size from settings.yaml)
make stage2

# Force recrawl specific URLs
make recrawl URL='/blog/*'
make recrawl URL='https://example.com/specific-page'
```

### Stage 3: Process Content ✅
Chunks text into manageable pieces for embedding. Features intelligent markdown-aware chunking.

Features:
- Configurable chunk sizes
- Respects sentence and paragraph boundaries
- Preserves markdown heading context
- Tracks staleness for re-processing
- Separate chunks database

```bash
# Process all crawled pages into chunks
make stage3

# View chunk statistics
make stats

# Preview sample chunks
make show-chunks
```

### Stage 4: Generate Embeddings ✅
Creates vector embeddings for semantic search using sentence-transformers.

Features:
- Configurable models (default: all-mpnet-base-v2, 768-dim)
- Smart batch processing
- Tracks embedding staleness
- Automatic re-embedding when chunks or model changes
- Separate embeddings database

```bash
# Generate embeddings (uses batch_size from settings.yaml)
make stage4

# View statistics
make stats

# Preview sample embeddings
make show-embeddings

# To switch models, edit settings.yaml:
# embeddings:
#   model: "all-MiniLM-L6-v2"
#   dimension: 384
# Then run: make stage4
```

## 🤝 Contributing

Contributions are welcome! This project aims to be educational and accessible. When contributing:

1. Keep code simple and well-commented
2. Write as if explaining to a junior developer
3. Test on modest hardware when possible
4. Update documentation for any new features

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Built with [Crawl4AI](https://github.com/unclecode/crawl4ai)
- Uses SQLite for simple, portable storage
- Inspired by the need for accessible RAG implementations

## 📧 Support

Found a bug? Have a question? [Open an issue](https://github.com/yourusername/simple-rag-pipeline/issues)

---

**Status**: 🚧 Stages 1-3 Complete | Stage 4 In Development
