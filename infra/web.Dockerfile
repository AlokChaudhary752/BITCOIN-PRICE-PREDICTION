# ==========================================
# STAGE 1: Frontend Build
# ==========================================
FROM node:20-alpine AS builder

WORKDIR /build

COPY apps/web/package*.json ./apps/web/
COPY packages/shared ./packages/shared/

WORKDIR /build/apps/web
RUN npm ci

COPY apps/web ./
RUN npm run build

# ==========================================
# STAGE 2: High-Performance Nginx Serving
# ==========================================
FROM nginx:1.27-alpine AS runner

COPY --from=builder /build/apps/web/dist /usr/share/nginx/html
COPY infra/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
