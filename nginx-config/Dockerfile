# Nginx container for Market Pie5 Bot behind Cloudflare Tunnel (cf_alfa).
# Proxies to frontend CONTAINER (market-pie5-bot-frontend:80) on tunnel_network.
# Tunnel route: market-bot.example.com → http://market-bot-nginx:80
FROM nginx:alpine
RUN apk add --no-cache curl
COPY market-bot-cloudflare-docker.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:80/ -o /dev/null || exit 1
CMD ["nginx", "-g", "daemon off;"]
