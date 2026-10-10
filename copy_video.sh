#!/bin/bash
# Script to copy video file from Windows to Linux

SOURCE_WINDOWS="C:\Users\operator\\Downloads\\grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4"
DEST_DIR="/home/operator/market-bot/market-pie5-bot/frontend/public/assets/video"
DEST_FILE="$DEST_DIR/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4"

echo "=========================================="
echo "Video File Copy Script"
echo "=========================================="
echo ""

# Try WSL path (most common)
WSL_PATHS=(
    "/mnt/c/Users/operator/Downloads/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4"
    "/c/Users/operator/Downloads/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4"
    "/home/operator/Downloads/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4"
)

FOUND=0
for path in "${WSL_PATHS[@]}"; do
    if [ -f "$path" ]; then
        echo "✓ Found video file at: $path"
        echo "Copying to: $DEST_FILE"
        
        # Create destination directory
        mkdir -p "$DEST_DIR"
        
        # Copy file
        cp "$path" "$DEST_FILE"
        
        if [ $? -eq 0 ]; then
            echo "✓ Video file copied successfully!"
            ls -lh "$DEST_FILE"
            FOUND=1
            break
        else
            echo "✗ Failed to copy file"
            exit 1
        fi
    fi
done

if [ $FOUND -eq 0 ]; then
    echo "⚠ Video file not found in common locations"
    echo ""
    echo "Please copy the file manually:"
    echo "  Source: $SOURCE_WINDOWS"
    echo "  Destination: $DEST_FILE"
    echo ""
    echo "Options:"
    echo "1. If using WSL, the file should be at:"
    echo "   /mnt/c/Users/operator/Downloads/grok-video-*.mp4"
    echo ""
    echo "2. Copy via command:"
    echo "   cp /mnt/c/Users/operator/Downloads/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4 $DEST_FILE"
    echo ""
    echo "3. Or use SCP/SFTP if on different machines"
    exit 1
fi

echo ""
echo "=========================================="
echo "Video file is ready!"
echo "The video background will now work."
echo "=========================================="
