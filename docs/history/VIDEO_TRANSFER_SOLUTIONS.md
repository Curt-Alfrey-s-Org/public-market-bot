# Video File Transfer Solutions

## Current Situation

The file is on Windows at:
```
C:\Users\operator\Downloads\grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4
```

The Linux machine cannot access Windows files via `/mnt/c/` because:
- This is a separate Linux machine (not WSL)
- Windows files are not mounted on this Linux system

---

## Solution Options

### Option 1: Use SCP from Windows PowerShell

**On Windows PowerShell, run:**

```powershell
# Replace 'your-linux-ip' with your Linux machine's IP address
# Or use 'localhost' if using SSH tunnel
scp "C:\Users\operator\Downloads\grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4" `
    operator@your-linux-ip:/home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/
```

**To find your Linux IP:**
```bash
# On Linux, run:
hostname -I
# or
ip addr show
```

---

### Option 2: Use WinSCP (GUI - Easiest)

1. **Download WinSCP:** https://winscp.net/
2. **Install and open WinSCP**
3. **Connect to Linux:**
   - Host: Your Linux IP address
   - Username: operator
   - Password: Your Linux password
   - Protocol: SFTP
4. **Navigate to:** `/home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/`
5. **Drag and drop** the video file from Windows

---

### Option 3: Use FileZilla (Alternative GUI)

1. **Download FileZilla:** https://filezilla-project.org/
2. **Connect via SFTP** to your Linux machine
3. **Navigate to destination directory**
4. **Upload the file**

---

### Option 4: Use USB Drive or Network Share

1. Copy file from Windows to USB drive
2. Plug USB into Linux machine
3. Mount USB (usually auto-mounted)
4. Copy from USB to destination:

```bash
# Find USB mount point (usually /media/operator/...)
ls /media/operator/

# Copy from USB
cp /media/operator/USB_NAME/grok-video-*.mp4 \
   /home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/
```

---

### Option 5: Use Python HTTP Server (Temporary)

**On Windows PowerShell:**
```powershell
# Navigate to Downloads folder
cd C:\Users\operator\Downloads

# Start simple HTTP server
python -m http.server 8000
```

**On Linux:**
```bash
# Get Windows machine IP address
# Then download the file
wget https://WINDOWS_IP:8000/ \
     -O /home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4
```

---

## Verify After Transfer

Once the file is transferred, verify:

```bash
ls -lh /home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/
```

You should see the video file with its size.

---

## Recommended Method

**For easiest transfer, use WinSCP** - it's a GUI tool that makes file transfer simple.

---

**Status:** Waiting for file transfer via one of the methods above.
