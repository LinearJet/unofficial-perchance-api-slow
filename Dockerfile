# Dockerfile for Render deployment
FROM python:3.11-slim

# Install system dependencies including Chromium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright and browsers
RUN pip install playwright
RUN playwright install chromium --with-deps

# Copy application code
COPY . .

# Copy pre-configured browser profile (with NSFW toggle enabled)
COPY automation_profile/ ./automation_profile/

# Set environment variables
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_BIN=/usr/bin/chromium
ENV DISPLAY=:99

# Expose port
EXPOSE 8000

# Create startup script
RUN echo '#!/bin/bash\nuvicorn main:app --host 0.0.0.0 --port $PORT' > start.sh && chmod +x start.sh

CMD ["./start.sh"]