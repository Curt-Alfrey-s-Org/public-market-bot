# Video Upload Instructions

## Video File Location

**Source (Windows):**
```
C:\Users\operator\Downloads\grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4
```

**Destination (Linux):**
```
/home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4
```

---

## How to Copy the Video File

Since the file is on a Windows system and we're on Linux, you have several options:

### Option 1: Using WSL/Windows Subsystem for Linux (If Available)

If you're using WSL, you can access Windows files directly:

```bash
# Copy from Windows to Linux (WSL)
cp /mnt/c/Users/operator/Downloads/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4 \
   /home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/

# Verify the file was copied
ls -lh /home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/
```

### Option 2: Using SCP/SFTP (If Windows and Linux are on different machines)

```bash
# From Windows machine, copy to Linux:
scp "c:\Users\operator\Downloads\grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4" \
    operator@your-linux-ip:/home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/
```

### Option 3: Using Shared Folder/Network Drive

If you have a shared folder or network drive:

```bash
# Mount the shared folder, then copy
cp /path/to/shared/grok-video-*.mp4 \
   /home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/
```

### Option 4: Manual Copy via USB/External Drive

1. Copy file from Windows to USB drive
2. Mount USB drive on Linux
3. Copy from USB to destination:

```bash
cp /media/usb/grok-video-*.mp4 \
   /home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/
```

### Option 5: Using File Manager (GUI)

If you have a GUI file manager:
1. Open file manager
2. Navigate to Windows Downloads folder (if accessible)
3. Navigate to `/home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/`
4. Copy and paste the file

---

## Verify Installation

After copying, verify the file is in place:

```bash
ls -lh /home/operator/market-bot/market-pie5-bot/frontend/public/assets/video/grok-video-*.mp4
```

You should see the file with its size.

---

## Video Background Configuration

The video background is already configured in:
- `frontend/src/components/VideoBackground.tsx`
- `frontend/src/App.tsx` (imported and used)

The video will:
- Auto-play on page load
- Loop continuously
- Be muted (required for autoplay)
- Cover full screen
- Have a dark overlay (40% opacity) for text readability

---

## Troubleshooting

### Video Not Showing?

1. **Check file exists:**
   ```bash
   ls -lh frontend/public/assets/video/
   ```

2. **Check file permissions:**
   ```bash
   chmod 644 frontend/public/assets/video/*.mp4
   ```

3. **Check browser console** for video loading errors

4. **Verify path in VideoBackground.tsx:**
   - Default path: `/assets/video/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4`
   - Files in `frontend/public/` are served at root `/`

### Video Path Issues?

If the video is in a different location, update `VideoBackground.tsx`:

```tsx
<VideoBackground 
  videoPath="/your/custom/path/video.mp4"
  enabled={true} 
/>
```

---

**Status:** Ready for video file upload
