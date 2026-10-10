# Video Background Fix

## Issues Fixed

1. **Path Issue:** Fixed video path to use Dash asset serving (`/assets/video/...` instead of file system path)
2. **Video Element:** Updated to use `100vw` and `100vh` for full viewport coverage
3. **Conditional Rendering:** Added proper checks to ensure video only renders when file exists

## Current Status

✅ **Code Fixed** - Video background implementation is correct  
⚠️ **File Missing** - Video file needs to be uploaded

## Video File Location

The video file needs to be placed at:
```
/home/operator/market-bot/market-pie5-bot/assets/video/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4
```

## How to Upload Video

### Option 1: From Windows (if using WSL or SSH)
```bash
# From WSL or SSH session
cp /mnt/c/Users/operator/Downloads/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4 \
   /home/operator/market-bot/market-pie5-bot/assets/video/
```

### Option 2: Using SCP (from Windows PowerShell)
```powershell
scp "C:\Users\operator\Downloads\grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4" \
    user@server:/home/operator/market-bot/market-pie5-bot/assets/video/
```

### Option 3: Manual Transfer
1. Use USB drive or network share
2. Copy file to `/home/operator/market-bot/market-pie5-bot/assets/video/`

## Verification

After uploading, verify the file exists:
```bash
ls -lh /home/operator/market-bot/market-pie5-bot/assets/video/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4
```

Then restart the web GUI - the video should appear on:
- ✅ Splash screen (behind the welcome message)
- ✅ Main dashboard background (behind all content)

## Video Features

- **Best Fit:** Uses `object-fit: cover` to fill entire screen while maintaining aspect ratio
- **Auto-play:** Starts automatically when page loads
- **Loop:** Continuously loops
- **Muted:** Required for autoplay in browsers
- **Full Screen:** Covers entire viewport (100vw x 100vh)
- **Non-intrusive:** Clicks pass through to UI elements

## Troubleshooting

If video still doesn't show:

1. **Check file exists:**
   ```bash
   ls -lh assets/video/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4
   ```

2. **Check file permissions:**
   ```bash
   chmod 644 assets/video/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4
   ```

3. **Check browser console** for video loading errors

4. **Verify video format:** MP4 (H.264) recommended for best browser compatibility

5. **Check Dash is serving assets:**
   - Visit: `https://localhost:8050/
   - Should download/play the video if serving correctly

## Code Changes

### Path Fix
- **Before:** `assets/video/grok-video-...` (file system path)
- **After:** `/assets/video/grok-video-...` (Dash asset URL path)

### Size Fix
- **Before:** `width: '100%', height: '100%'`
- **After:** `width: '100vw', height: '100vh'` (full viewport)

### Conditional Check
- Added check for `VIDEO_BACKGROUND_PATH` in addition to `VIDEO_BACKGROUND_ENABLED`
