# 🚀 MANUAL WEBSITE DEPLOYMENT - Step by Step

## Status
Your bot dashboard is **READY TO DEPLOY** but requires manual steps on the webserver.

## What You Need to Do

### Step 1: Connect to Webserver
```bash
ssh operator@192.0.2.21
```

### Step 2: Install Nginx & SSL Tools
Run this on the webserver:
```bash
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### Step 3: Configure Nginx
Run this on the webserver:
```bash
sudo cp /tmp/nginx-market-pie5-bot.conf /etc/nginx/sites-available/market-pie5-bot
sudo ln -sf /etc/nginx/sites-available/market-pie5-bot /etc/nginx/sites-enabled/market-pie5-bot
```

### Step 4: Test & Enable
```bash
# Test the configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Enable on boot
sudo systemctl enable nginx
```

### Step 5: Get SSL Certificate
```bash
sudo certbot certonly --nginx -d market-bot.example.com
```

When prompted:
- Email: use your email
- Agree to terms: (A)gree
- Share email: (Y)es or (N)o (your choice)

### Step 6: Verify It Works
Still on the webserver:
```bash
curl -I https://market-bot.example.com/
```

You should see: `HTTP/2 200` or similar (not an error)

## Testing from Local Machine

After all steps above complete:
```bash
# Check the website
curl -I https://market-bot.example.com/

# View bot status API
curl https://market-bot.example.com/api/bot/status

# Check the dashboard in browser
open https://market-bot.example.com/
```

## What Gets Deployed

Your website will serve:
- ✅ Live trading dashboard (HTML UI)
- ✅ API endpoints for bot data
- ✅ Real-time trade updates
- ✅ WebSocket for live metrics
- ✅ HTTPS/SSL secured
- ✅ Auto-refresh every 30 seconds

## Files Already On Webserver

- `/tmp/nginx-market-pie5-bot.conf` - Nginx configuration
- `/tmp/install_nginx_reverse_proxy.sh` - Installation script

## Architecture
```
Your Domain (Cloudflare DNS)
        ↓
Nginx Reverse Proxy (192.0.2.21)
        ↓ (internal, port 8000)
Bot API (operator, 192.0.2.21:8004)
        ↓
Trading Bot (main.py)
```

## Troubleshooting

### If nginx -t fails:
```bash
sudo cat /etc/nginx/sites-available/market-pie5-bot
# Check for syntax errors
```

### If certbot fails:
```bash
# Make sure port 80 and 443 are open
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### If still not accessible:
Check firewall on bot server:
```bash
# On operator (192.0.2.21):
sudo ufw allow 8000/tcp from 192.0.2.21
```

## Once Live

Your bot's dashboard will be publicly visible at:
🌐 **https://market-bot.example.com/**

Anyone can watch your trades, see P&L, and track performance in real-time!

---

**Need help?** Check `WEBSITE_DEPLOYMENT_GUIDE.md` for detailed troubleshooting.
