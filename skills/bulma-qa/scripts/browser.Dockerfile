FROM node:22-bookworm-slim@sha256:e9f565d32859f0cbfb52125eafe8be39390f24dac302dc3cdf566e8ba3ab21ee
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates chromium curl fonts-liberation tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
RUN npm install --global agent-browser@0.27.0
