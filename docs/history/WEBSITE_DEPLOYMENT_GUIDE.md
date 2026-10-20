# Website Deployment Guide - Market Pie5 Bot Dashboard

## Overview
Your bot dashboard is now ready to be served on the public website: **https://market-bot.example.com**

The dashboard needs to be deployed on the **webserver** (192.0.2.21) as a reverse proxy to your **bot API** running on operator (192.0.2.21:8004).

## Deployment Steps

### Step 1: Run Installation Script on Webserver

1. SSH into the webserver:
```bash
ssh operator@192.0.2.21
```

2. Run the installation script:
```bash
sudo bash /tmp/install_nginx_reverse_proxy.sh
```

This will:
- ✅ Install Nginx reverse proxy configuration
- ✅ Enable the site
- ✅ Test the configuration
- ✅ Reload Nginx

### Step 2: Obtain SSL Certificate

After the script completes, run:
```bash
sudo certbot certonly --nginx -d market-bot.example.com
```

This will:
- ✅ Get a free SSL certificate from Let's Encrypt
- ✅ Automatically configure Nginx to use it
- ✅ Enable HTTPS on the domain

### Step 3: Verify Deployment

Test the website is accessible:
```bash
# From your local machine:
curl -I https://market-bot.example.com/

# Check bot status:
curl https://market-bot.example.com/api/bot/status

# View dashboard in browser:
# Open: https://market-bot.example.com/
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Internet / Cloudflare DNS                              │
│  market-bot.example.com                     │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS/SSL
                     ↓
┌─────────────────────────────────────────────────────────┐
│  Webserver (192.0.2.21)                              │
│  Nginx Reverse Proxy                                    │
│  - Listens on :443 (HTTPS)                              │
│  - Forwards to bot API                                  │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP (internal)
                     ↓
┌─────────────────────────────────────────────────────────┐
│  Bot Server (operator - 192.0.2.21:8004)                 │
│  FastAPI + Uvicorn                                      │
│  - Serves dashboard HTML                                │
│  - Provides /api/* endpoints                            │
│  - WebSocket for real-time updates                      │
└─────────────────────────────────────────────────────────┘
```

## What Gets Served

### Root Path: `/`
- **HTML Dashboard** with purple gradient UI
- Shows: Bot status, trades, P&L, performance metrics
- Auto-refreshes every 30 seconds
- Real-time WebSocket updates

### API Endpoints: `/api/*`
- `/api/bot/status` - Bot running status
- `/api/stats` - Performance statistics
- `/api/trades` - Recent trades and P&L
- `/api/health` - API health check
- `/docs` - Swagger API documentation

### Static Files: `/static/*`
- CSS, JavaScript, assets
- Dashboard UI components

## Troubleshooting

### If deployment fails:

1. **Check Nginx is running:**
```bash
sudo systemctl status nginx
```

2. **Check bot API is accessible from webserver:**
```bash
curl -I http://192.0.2.21:8004/
```

3. **View Nginx error logs:**
```bash
sudo tail -f /var/log/nginx/market-pie5-bot-error.log
```

4. **Test Nginx config:**
```bash
sudo nginx -t
```

5. **Check firewall rules:**
```bash
# Make sure port 8000 is accessible from webserver to operator
# On operator:
sudo ufw allow 8000/tcp from 192.0.2.21
```

### SSL Certificate Issues:

If certbot fails, check:
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

## After Deployment

Your dashboard will be live at:
- 🌐 **https://market-bot.example.com/**
- 📊 **Live trades and metrics** visible to anyone with the URL
- 🔒 **SSL/HTTPS** secured (no sensitive data exposed)
- 🚀 **Real-time updates** via WebSocket

The public can view your bot's trading activity, performance metrics, and trades in real-time!

## Next Steps

1. ✅ Run installation script on webserver
2. ✅ Set up SSL certificate
3. ✅ Test the website: https://market-bot.example.com/
4. ✅ Monitor bot trading live on the public dashboard

The bot is already running and collecting trades - the website will start displaying them immediately once deployed!
