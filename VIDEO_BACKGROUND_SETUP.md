# Video Background Setup Guide

## Overview

The web GUI now supports a hardcoded video background. The video file `grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4` is configured to be used as the background with "best fit" (object-fit: cover) styling.

## File Location

The video file should be placed at:
```
assets/video/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4
```

## Setup Instructions

### Step 1: Copy the Video File

If you're on Windows and the file is at:
```
C:\Users\operator\Downloads\grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4
```

You need to copy it to the Linux system. Options:

**Option A: Using SCP (from Windows)**
```bash
scp "C:\Users\operator\Downloads\grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4" user@linux-server:/home/operator/market-bot/market-pie5-bot/assets/video/
```

**Option B: Using WSL (if available)**
```bash
# From WSL
cp /mnt/c/Users/operator/Downloads/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4 /home/operator/market-bot/market-pie5-bot/assets/video/
```

**Option C: Manual Transfer**
1. Use a USB drive or network share
2. Copy the file to `/home/operator/market-bot/market-pie5-bot/assets/video/`

### Step 2: Verify File Location

After copying, verify the file exists:
```bash
ls -lh /home/operator/market-bot/market-pie5-bot/assets/video/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4
```

### Step 3: Restart Web GUI

The video background will automatically be used if the file exists. No configuration needed!

## Features

- **Best Fit**: Uses `object-fit: cover` CSS property to ensure the video covers the entire background while maintaining aspect ratio
- **Auto-play**: Video automatically plays when the page loads
- **Loop**: Video loops continuously
- **Muted**: Video is muted (required for autoplay in most browsers)
- **No Controls**: Video controls are hidden
- **Non-intrusive**: Video has `pointer-events: none` so clicks pass through to UI elements
- **Opacity Control**: Respects `BACKGROUND_OPACITY` setting (default: 1.0)

## Fallback Behavior

If the video file is not found:
- The system will automatically fall back to the image background (if configured)
- Or use the default solid color background

## Code Configuration

The video path is hardcoded in `web_gui.py`:

```python
VIDEO_BACKGROUND_PATH = os.path.join('assets', 'video', 'grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4')
VIDEO_BACKGROUND_ENABLED = os.path.exists(VIDEO_BACKGROUND_PATH)
```

## Troubleshooting

### Video Not Showing

1. **Check file exists:**
   ```bash
   ls -lh assets/video/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4
   ```

2. **Check file permissions:**
   ```bash
   chmod 644 assets/video/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4
   ```

3. **Check browser console** for video loading errors

4. **Verify video format** - MP4 (H.264) is recommended for best browser compatibility

### Video Not Fitting Properly

The video uses `object-fit: cover` which:
- Maintains aspect ratio
- Covers entire viewport
- May crop edges if aspect ratios don't match

To adjust, modify the `objectFit` property in `get_video_background_element()` function.

### Performance Issues

If the video causes performance issues:
1. Reduce video resolution/bitrate
2. Use a shorter video file
3. Consider using a static image instead
4. Adjust `BACKGROUND_OPACITY` to reduce visual impact

## Notes

- The video background works on both the splash screen and main dashboard
- Video is positioned behind all UI elements (z-index: -1)
- Video will not interfere with user interactions
- The video path is relative to the web GUI's working directory
