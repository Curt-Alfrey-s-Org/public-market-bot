/* Draggable Widgets System for Market Pie5 Bot */
/* Implements HTML5 drag-and-drop with position persistence */

(function() {
    'use strict';
    
    let draggedElement = null;
    let layoutData = {};
    
    // Initialize drag-and-drop on page load
    function initializeDragAndDrop() {
        console.log('Initializing drag-and-drop system...');
        
        // Load saved layout from localStorage
        loadLayout();
        
        // Setup all draggable widgets
        setupDraggableWidgets();
        
        // Setup layout control buttons
        setupLayoutControls();
        
        console.log('Drag-and-drop system initialized');
    }
    
    // Setup draggable functionality for all widgets
    function setupDraggableWidgets() {
        const widgets = document.querySelectorAll('.draggable-widget');
        
        widgets.forEach((widget, index) => {
            // Make element draggable
            widget.setAttribute('draggable', 'true');
            widget.dataset.widgetId = widget.id || `widget-${index}`;
            
            // Add drag event listeners
            widget.addEventListener('dragstart', handleDragStart);
            widget.addEventListener('dragend', handleDragEnd);
            widget.addEventListener('dragover', handleDragOver);
            widget.addEventListener('drop', handleDrop);
            widget.addEventListener('dragenter', handleDragEnter);
            widget.addEventListener('dragleave', handleDragLeave);
            
            // Add widget controls
            setupWidgetControls(widget);
        });
    }
    
    // Handle drag start
    function handleDragStart(e) {
        draggedElement = this;
        this.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', this.innerHTML);
    }
    
    // Handle drag end
    function handleDragEnd(e) {
        this.classList.remove('dragging');
        
        // Remove drag-over class from all widgets
        document.querySelectorAll('.draggable-widget').forEach(widget => {
            widget.classList.remove('drag-over');
        });
        
        // Save layout after drag
        saveLayout();
        
        draggedElement = null;
    }
    
    // Handle drag over
    function handleDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault();
        }
        e.dataTransfer.dropEffect = 'move';
        return false;
    }
    
    // Handle drag enter
    function handleDragEnter(e) {
        if (this !== draggedElement) {
            this.classList.add('drag-over');
        }
    }
    
    // Handle drag leave
    function handleDragLeave(e) {
        this.classList.remove('drag-over');
    }
    
    // Handle drop
    function handleDrop(e) {
        if (e.stopPropagation) {
            e.stopPropagation();
        }
        
        if (draggedElement !== this) {
            // Swap positions in DOM
            const parent = draggedElement.parentNode;
            const draggedIndex = Array.from(parent.children).indexOf(draggedElement);
            const targetIndex = Array.from(parent.children).indexOf(this);
            
            if (draggedIndex < targetIndex) {
                parent.insertBefore(draggedElement, this.nextSibling);
            } else {
                parent.insertBefore(draggedElement, this);
            }
        }
        
        this.classList.remove('drag-over');
        return false;
    }
    
    // Setup widget controls (collapse, close, etc.)
    function setupWidgetControls(widget) {
        const header = widget.querySelector('.widget-header');
        if (!header) return;
        
        const controls = header.querySelector('.widget-controls');
        if (!controls) return;
        
        // Collapse button
        const collapseBtn = controls.querySelector('[data-action="collapse"]');
        if (collapseBtn) {
            collapseBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                widget.classList.toggle('widget-collapsed');
                const icon = collapseBtn.querySelector('i');
                if (icon) {
                    icon.className = widget.classList.contains('widget-collapsed') 
                        ? 'fas fa-chevron-down' 
                        : 'fas fa-chevron-up';
                }
                saveLayout();
            });
        }
        
        // Settings button
        const settingsBtn = controls.querySelector('[data-action="settings"]');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                // Open widget settings (can be implemented later)
                console.log('Widget settings clicked:', widget.dataset.widgetId);
            });
        }
        
        // Close button (hide widget)
        const closeBtn = controls.querySelector('[data-action="close"]');
        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                widget.style.display = 'none';
                saveLayout();
            });
        }
    }
    
    // Setup layout control buttons
    function setupLayoutControls() {
        const resetBtn = document.getElementById('reset-layout-button');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                resetLayout();
            });
        }
        
        const saveBtn = document.getElementById('save-layout-button');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                saveLayout();
                showNotification('Layout saved successfully!', 'success');
            });
        }
    }
    
    // Save layout to localStorage
    function saveLayout() {
        const widgets = document.querySelectorAll('.draggable-widget');
        const layout = [];
        
        widgets.forEach((widget, index) => {
            layout.push({
                id: widget.dataset.widgetId,
                order: index,
                collapsed: widget.classList.contains('widget-collapsed'),
                hidden: widget.style.display === 'none',
                size: widget.className.match(/widget-(small|medium|large|full)/)?.[1] || 'medium'
            });
        });
        
        localStorage.setItem('mp5-dashboard-layout', JSON.stringify(layout));
        console.log('Layout saved:', layout);
    }
    
    // Load layout from localStorage
    function loadLayout() {
        const savedLayout = localStorage.getItem('mp5-dashboard-layout');
        if (!savedLayout) return;
        
        try {
            layoutData = JSON.parse(savedLayout);
            console.log('Layout loaded:', layoutData);
            applyLayout();
        } catch (e) {
            console.error('Error loading layout:', e);
        }
    }
    
    // Apply saved layout
    function applyLayout() {
        if (!layoutData || layoutData.length === 0) return;
        
        const grid = document.querySelector('.dashboard-grid');
        if (!grid) return;
        
        // Sort widgets by saved order
        const sortedWidgets = layoutData
            .map(item => document.querySelector(`[data-widget-id="${item.id}"]`))
            .filter(widget => widget !== null);
        
        // Reorder widgets in DOM
        sortedWidgets.forEach((widget, index) => {
            const savedData = layoutData.find(item => item.id === widget.dataset.widgetId);
            if (savedData) {
                // Apply collapsed state
                if (savedData.collapsed) {
                    widget.classList.add('widget-collapsed');
                    const collapseBtn = widget.querySelector('[data-action="collapse"] i');
                    if (collapseBtn) {
                        collapseBtn.className = 'fas fa-chevron-down';
                    }
                }
                
                // Apply hidden state
                if (savedData.hidden) {
                    widget.style.display = 'none';
                }
            }
            
            grid.appendChild(widget);
        });
    }
    
    // Reset layout to default
    function resetLayout() {
        if (confirm('Reset dashboard layout to default? This will restore all widgets to their original positions.')) {
            localStorage.removeItem('mp5-dashboard-layout');
            
            // Show all widgets
            document.querySelectorAll('.draggable-widget').forEach(widget => {
                widget.style.display = '';
                widget.classList.remove('widget-collapsed');
            });
            
            // Reload page to restore default order
            window.location.reload();
        }
    }
    
    // Show notification
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#10b981' : '#1d9bf0'};
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            animation: slideInRight 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeDragAndDrop);
    } else {
        // DOM is already ready
        initializeDragAndDrop();
    }
    
    // Re-initialize on Dash callback updates
    if (window.dash_clientside) {
        window.dash_clientside.draggableWidgets = {
            reinitialize: function() {
                setTimeout(initializeDragAndDrop, 100);
                return window.dash_clientside.no_update;
            }
        };
    }
    
    // Export for external use
    window.MP5DragDrop = {
        saveLayout: saveLayout,
        loadLayout: loadLayout,
        resetLayout: resetLayout
    };
    
})();

/* Notification animations */
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
