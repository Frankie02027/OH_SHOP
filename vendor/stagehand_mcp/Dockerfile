# Dockerfile for the extracted Stagehand MCP runtime slice.
# Build context: vendor/stagehand_mcp
FROM node:20-slim

# Install system Chromium + deps. Stagehand uses chrome-launcher internally,
# which auto-discovers /usr/bin/chromium on the system PATH.
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libasound2 \
    libxshmfence1 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_PATH=/usr/bin/chromium
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

WORKDIR /app

# Copy package manifest, lockfile, and tsconfig
COPY package.json package-lock.json tsconfig.json ./

# Install deps deterministically from the checked-in lockfile.
RUN npm ci --no-audit --no-fund

# Copy source
COPY src/ src/

# Build
RUN npx tsc

ENV NODE_ENV=production
ENV MCP_PORT=3020
EXPOSE 3020

HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=15s \
  CMD node -e "fetch('http://127.0.0.1:3020/healthz').then(r=>{if(!r.ok)throw 1}).catch(()=>process.exit(1))"

CMD ["node", "dist/server.js"]
