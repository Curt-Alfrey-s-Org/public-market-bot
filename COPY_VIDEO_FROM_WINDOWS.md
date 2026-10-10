# Copy Video from Windows to Linux

## You're on Windows PowerShell

Since you're running PowerShell on Windows and need to copy to a Linux machine, use one of these methods:

---

## Method 1: Using SCP (Secure Copy) from PowerShell

**Prerequisites:** 
- SSH access to Linux machine
- SCP installed (comes with OpenSSH on Windows 10/11)

**Command:**
```powershell
scp "C:\Users\operator\Downloads\grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4" `
    operator@your-linux-ip:/home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/
```

**Replace:**
- `your-linux-ip` with your Linux machine's IP address or hostname
- Or use `localhost` if using WSL

---

## Method 2: Using WSL (If Windows Subsystem for Linux is installed)

If you have WSL installed, open WSL terminal and run:

```bash
# In WSL terminal (not PowerShell)
cp /mnt/c/Users/operator/Downloads/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4 \
   /home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/
```

**To open WSL:**
- Type `wsl` in PowerShell, or
- Open "Ubuntu" or your Linux distro from Start menu

---

## Method 3: Using WinSCP (GUI Tool)

1. Download WinSCP: https://winscp.net/
2. Connect to your Linux machine
3. Navigate to: `/home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/`
4. Drag and drop the video file from Windows

---

## Method 4: Using FileZilla (FTP/SFTP)

1. Download FileZilla: https://filezilla-project.org/
2. Connect via SFTP to your Linux machine
3. Navigate to the destination directory
4. Upload the video file

---

## Method 5: Using Shared Network Drive

If you have a shared folder or network drive:

1. Map the Linux directory as a network drive
2. Copy the file using Windows Explorer

---

## Verify After Copy

Once copied, verify on Linux:

```bash
ls -lh /home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/
```

---

**Note:** The `/mnt/c/` path only works inside WSL, not in PowerShell!
