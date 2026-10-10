#!/bin/bash
# Deploy dashboard to public website via reverse proxy

set -e

WEBSERVER_IP="${WEBSERVER_IP:-192.0.2.21}"
BOT_IP="${BOT_IP:-192.0.2.21}"
BOT_PORT="${API_PORT:-8001}"
DOMAIN="market-bot.example.com"

echo "=========================================="
echo "Deploying Dashboard to Public Website"
echo "=========================================="
echo ""
echo "Setup:"
echo "  - Webserver: $WEBSERVER_IP"
echo "  - Bot API: $BOT_IP:$BOT_PORT"
echo "  - Domain: $DOMAIN"
echo ""

# Create Nginx reverse proxy config
NGINX_CONFIG="/etc/nginx/sites-available/market-pie5-bot"
NGINX_ENABLED="/etc/nginx/sites-enabled/market-pie5-bot"

echo "🔧 Creating Nginx reverse proxy config..."

cat > /tmp/nginx-market-pie5-bot.conf << 'NGINX_EOF'
# Reverse proxy to Market Pie5 Bot API
# Forward traffic from market-bot.example.com to the bot API

upstream bot_api {
    server 192.0.2.21:8001;
    keepalive 32;
}

server {
    listen 80;
    server_name market-bot.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name market-bot.example.com;
    
    # SSL certificates managed by Certbot/Let's Encrypt
    ssl_certificate /etc/letsencrypt/live/market-bot.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/market-bot.example.com/privkey.pem;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Logging
    access_log /var/log/nginx/market-pie5-bot-access.log;
    error_log /var/log/nginx/market-pie5-bot-error.log;
    
    # Root location - serve dashboard
    location / {
        proxy_pass http://bot_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://bot_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket support for real-time updates
    location /ws {
        proxy_pass http://bot_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
    
    # Static files and docs
    location /static/ {
        proxy_pass http://bot_api;
        proxy_set_header Host $host;
        expires 1h;
    }
    
    location /docs {
        proxy_pass http://bot_api;
        proxy_set_header Host $host;
    }
}
NGINX_EOF

echo "✓ Config created at /tmp/nginx-market-pie5-bot.conf"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Copy config to webserver:"
echo "   scp /tmp/nginx-market-pie5-bot.conf operator@$WEBSERVER_IP:/tmp/"
echo ""
echo "2. On webserver, install config:"
echo "   sudo cp /tmp/nginx-market-pie5-bot.conf $NGINX_CONFIG"
echo "   sudo ln -sf $NGINX_CONFIG $NGINX_ENABLED"
echo "   sudo nginx -t"
echo "   sudo systemctl reload nginx"
echo ""
echo "3. Set up SSL (on webserver):"
echo "   sudo certbot certonly --nginx -d market-bot.example.com"
echo ""
echo "4. Test:"
echo "   curl -I https://market-bot.example.com/"
echo ""
