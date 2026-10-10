#!/bin/bash
# Manual installation script - run this on the webserver (192.0.2.21)
# Copy this file to the webserver and run with: bash install_nginx_reverse_proxy.sh

echo "=========================================="
echo "Installing Nginx Reverse Proxy"
echo "=========================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use: sudo bash install_nginx_reverse_proxy.sh)"
   exit 1
fi

echo "1️⃣  Installing Nginx reverse proxy config..."
cp /tmp/nginx-market-pie5-bot.conf /etc/nginx/sites-available/market-pie5-bot
echo "   ✓ Config installed"

echo ""
echo "2️⃣  Enabling the site..."
ln -sf /etc/nginx/sites-available/market-pie5-bot /etc/nginx/sites-enabled/market-pie5-bot
echo "   ✓ Site enabled"

echo ""
echo "3️⃣  Testing Nginx config..."
nginx -t
if [ $? -ne 0 ]; then
    echo "   ❌ Config test failed!"
    exit 1
fi
echo "   ✓ Config is valid"

echo ""
echo "4️⃣  Reloading Nginx..."
systemctl reload nginx
echo "   ✓ Nginx reloaded"

echo ""
echo "5️⃣  Setting up SSL certificate..."
echo ""
echo "   Run this command to get an SSL cert from Let's Encrypt:"
echo "   sudo certbot certonly --nginx -d market-bot.example.com"
echo ""

echo "=========================================="
echo "✅ Nginx reverse proxy installed!"
echo "=========================================="
echo ""
echo "Your dashboard is now available at:"
echo "  🌐 http://market-bot.example.com/ (will be HTTPS after SSL setup)"
echo ""
echo "Test it:"
echo "  curl -I http://market-bot.example.com/"
echo ""
