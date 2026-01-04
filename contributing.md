# Contributing to Simple RAG Pipeline

Thank you for your interest in contributing! This project aims to be educational and accessible to developers of all skill levels.

## 🎯 Project Philosophy

1. **Simplicity First**: Code should be readable by junior developers
2. **Well Documented**: Every function needs clear docstrings
3. **Educational Value**: Prefer clarity over cleverness
4. **Resource Conscious**: Test on modest hardware when possible

## 📝 Code Style Guidelines

### Python Code

- **Keep it simple**: Write code a junior developer would write
- **Comment generously**: Explain the "why", not just the "what"
- **Use descriptive names**: `url_list` not `ul`, `fetch_sitemap()` not `fs()`
- **One function, one purpose**: Each function should do exactly one thing
- **Avoid advanced patterns**: No decorators, metaclasses, or complex comprehensions unless absolutely necessary

### Example of Good Code Style

```python
def fetch_sitemap(sitemap_url, user_agent):
    """
    Download the sitemap.xml file from the given URL.
    Returns the response content if successful, None otherwise.
    """
    headers = {'User-Agent': user_agent}
    
    try:
        print(f"Fetching sitemap from: {sitemap_url}")
        response = requests.get(sitemap_url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Error fetching sitemap: {e}")
        return None
```

## 🔧 Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/simple-rag-pipeline.git
cd simple-rag-pipeline

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
make setup

# Make your changes...

# Test your changes
make stage1
make stats
```

## 📋 Pull Request Process

1. **Create an issue first**: Describe what you want to add/fix
2. **Fork the repository**: Make changes in your fork
3. **Keep commits focused**: One feature/fix per PR
4. **Test thoroughly**: Ensure your code works on modest hardware
5. **Update documentation**: README, docstrings, comments
6. **Follow the style guide**: Keep code simple and well-commented

## 🐛 Reporting Bugs

When reporting bugs, please include:

- Your operating system and version
- Python version (`python3 --version`)
- Steps to reproduce the issue
- Expected vs actual behavior
- Any error messages or logs

## 💡 Suggesting Features

We love new ideas! When suggesting features:

- Explain the use case
- Consider if it fits the "simple and educational" philosophy
- Think about resource requirements
- Suggest how it might be implemented simply

## ✅ What We're Looking For

- Bug fixes
- Documentation improvements
- Performance optimizations (that don't sacrifice readability)
- New pipeline stages that follow existing patterns
- Better error handling
- More helpful output messages

## ❌ What We're Not Looking For

- Complex abstractions that reduce readability
- Features requiring external services (keep it self-contained)
- Dependencies on large frameworks
- Code that requires high-end hardware

## 🙏 Thank You!

Every contribution helps make this project more useful and accessible. Whether it's fixing a typo or adding a new feature, we appreciate your time and effort!
