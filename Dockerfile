FROM python:3.9-slim

# 1. Install system dependencies and Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 2. Set working directory
WORKDIR /app

# 3. Copy dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy project code
COPY . .

# 5. Expose port (Streamlit defaults to 8501, but HF Spaces uses 7860)
EXPOSE 7860

# 6. Start command
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
