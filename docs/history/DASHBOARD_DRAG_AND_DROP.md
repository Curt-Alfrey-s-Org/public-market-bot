# Dashboard Drag-and-Drop Feature

## Overview

Implemented a draggable dashboard system that allows users to rearrange widgets by dragging them. The layout is automatically saved to localStorage and persists across sessions.

## Features

### 1. Drag-and-Drop Functionality
- **Native HTML5 Drag API**: Uses browser's built-in drag-and-drop (no external dependencies)
- **Visual Feedback**: 
  - Drag handle appears on hover
  - Widget opacity changes while dragging
  - Smooth transitions

### 2. Layout Persistence
- **localStorage**: Dashboard layout is saved automatically
- **Auto-restore**: Layout is restored when page loads
- **Validation**: Missing widgets are automatically added back

### 3. User Experience
- **Hover to Reveal**: Drag handle only appears on hover (clean UI)
- **Visual Indicators**: 
  - Cursor changes to grab/grabbing
  - Opacity changes during drag
  - Smooth animations

## Implementation

### Components

**`DraggableDashboard.tsx`** - Main container component
- Manages widget order state
- Handles drag-and-drop events
- Saves/loads layout from localStorage

**`DraggableWidget`** - Individual draggable widget wrapper
- Wraps each dashboard widget
- Provides drag handle
- Handles drag events

### Widget Configuration

Widgets are defined in `Dashboard.tsx`:

```typescript
const widgets = [
  {
    id: 'mode-selector',
    title: 'Mode Selector',
    defaultOrder: 1,
    component: <ModeSelector ... />,
  },
  {
    id: 'stats-overview',
    title: 'Stats Overview',
    defaultOrder: 2,
    component: <StatsOverview />,
  },
  // ... more widgets
]
```

### Default Widget Order

1. Mode Selector
2. Stats Overview
3. Equity Curve Chart
4. P&L Trend Chart
5. Monthly Returns Chart

## Usage

1. **Hover** over any widget to see the drag handle (⋮⋮ icon)
2. **Click and drag** the handle to move the widget
3. **Drop** the widget in the desired position
4. Layout is **automatically saved** to localStorage

## Technical Details

### Drag Events Handled

- `onDragStart`: Initiates drag, sets dragged widget ID
- `onDragOver`: Prevents default, allows drop
- `onDrop`: Reorders widgets, saves to localStorage
- `onDragEnd`: Cleans up drag state

### State Management

- `widgetIds`: Array of widget IDs in current order
- `draggedId`: Currently dragged widget ID
- `dragOverId`: Widget being dragged over

### localStorage Key

- **Key**: `dashboard-layout`
- **Value**: JSON array of widget IDs in order
- **Example**: `["mode-selector", "stats-overview", "equity-chart", ...]`

## Benefits

✅ **No External Dependencies**: Uses native HTML5 drag API
✅ **Persistent Layout**: User preferences saved automatically
✅ **Clean UI**: Drag handles only visible on hover
✅ **Smooth UX**: Visual feedback during drag operations
✅ **Flexible**: Easy to add/remove widgets

## Future Enhancements

Potential improvements:
- Grid layout with resizable widgets
- Widget visibility toggles
- Multiple dashboard layouts
- Widget size customization
- Export/import dashboard layouts
