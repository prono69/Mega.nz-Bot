FROM python:3.11-alpine

# System deps
RUN apk add --no-cache \
    ffmpeg \
    git \
    gcc \
    musl-dev \
    linux-headers

# megatools (edge repo)
RUN apk add --no-cache --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing/ megatools

# Set working dir
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy rest of the code
COPY . .

# Run app
CMD ["python", "-m", "megadl"]
