FROM alpine:latest

RUN apk update && apk upgrade
RUN apk add --no-cache \
    python3 \
    py3-pip \
    gcc \
    python3-dev \
    musl-dev \
    linux-headers \
    git \
    ffmpeg

RUN apk add --no-cache --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing/ megatools

# Create venv OUTSIDE app
RUN python3 -m venv /venv

# Upgrade pip inside venv
RUN /venv/bin/pip install --upgrade pip

WORKDIR /app
COPY . .

# Install requirements in venv
RUN /venv/bin/pip install -U -r requirements.txt

CMD ["/venv/bin/python3", "-m", "megadl"]
