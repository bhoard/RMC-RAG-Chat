# Use Ubuntu 24.04 as base
FROM ubuntu:24.04

# 1. Environment Setup
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
# Pre-set the PATH so the virtual environment is always "active"
ENV PATH="/opt/venv/bin:$PATH"

# 2. Install Core Tools & Playwright System Dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    sqlite3 \
    make \
    git \
    curl \
    wget \
    sudo \
    # Playwright system dependencies for Ubuntu 24.04
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libxshmfence1 \
    libglib2.0-0 \
    libasound2t64 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. Initialize Virtual Environment
RUN python3 -m venv /opt/venv

# 4. Set Working Directory
WORKDIR /app

# 5. Install Python Dependencies
# We copy requirements first to keep the build fast
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Option 2: Install Playwright Browsers
# This baked-in approach saves time during runtime
# (Assuming 'playwright' is in your requirements.txt)
RUN playwright install chromium --with-deps

# Keep the container running
CMD ["python3"]