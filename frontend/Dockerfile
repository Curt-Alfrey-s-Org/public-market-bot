# syntax=docker/dockerfile:1
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

ARG NPM_REGISTRY=http://192.0.2.30

COPY package*.json ./
COPY vendor/ ./vendor/

# Shared npm cache across bot repos (BuildKit id=bots-npm).
# See /srv/dep-cache/README.md.
RUN --mount=type=cache,id=bots-npm,target=/root/.npm,sharing=locked \
    npm ci --registry "${NPM_REGISTRY}" --prefer-offline --no-audit --no-fund

COPY . .

# No API key is built into the bundle: anything in VITE_* ships to every
# browser. The app authenticates with the logged-in user's JWT instead.

RUN npm run build

# Runtime stage
FROM nginx:alpine

RUN --mount=type=cache,id=bots-apk,target=/var/cache/apk,sharing=locked \
    apk add --no-cache curl

# Copy nginx config for reverse proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built frontend
COPY --from=builder /app/dist /app/dist

EXPOSE 80

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

