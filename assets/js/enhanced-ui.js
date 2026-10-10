// Market Pie5 Bot - Enhanced JavaScript for Visual Appeal
// Node.js powered client-side enhancements

/**
 * Performance Notes:
 * - Animations use CSS where possible (GPU accelerated)
 * - JavaScript animations are throttled/debounced
 * - IntersectionObserver used for efficient scroll detection
 * - MutationObserver is targeted to specific elements
 * - Consider limiting number of animated elements for Raspberry Pi 5
 */

/**
 * Initialize enhanced visual features
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Market Pie5 Enhanced UI - Initializing...');
    
    // Add fade-in animation to elements as they appear
    initScrollAnimations();
    
    // Enhance number animations
    initNumberCounters();
    
    // Add smooth hover effects
    initInteractiveElements();
    
    // Initialize tooltips
    initTooltips();
    
    console.log('Market Pie5 Enhanced UI - Ready!');
});

/**
 * Animate elements as they scroll into view
 */
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                // Add staggered animation delay
                setTimeout(() => {
                    entry.target.classList.add('fade-in');
                }, index * 100);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe all cards and major sections
    document.querySelectorAll('.modern-card, .stat-card, .chart-container').forEach(el => {
        observer.observe(el);
    });
}

/**
 * Animate number changes with smooth counting
 */
function initNumberCounters() {
    const animateValue = (element, start, end, duration) => {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                current = end;
                clearInterval(timer);
            }
            
            // Format number based on context
            if (element.classList.contains('currency')) {
                element.textContent = '$' + current.toFixed(2);
            } else if (element.classList.contains('percentage')) {
                element.textContent = current.toFixed(1) + '%';
            } else {
                element.textContent = Math.round(current);
            }
        }, 16);
    };
    
    // Observe stat elements for changes
    const statObserver = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList' || mutation.type === 'characterData') {
                const element = mutation.target;
                if (element.classList && element.classList.contains('animate-number')) {
                    element.classList.add('count-up');
                }
            }
        });
    });
    
    // Watch all number elements
    document.querySelectorAll('.animate-number').forEach(el => {
        statObserver.observe(el, {
            childList: true,
            characterData: true,
            subtree: true
        });
    });
}

/**
 * Enhance interactive elements with better feedback
 */
function initInteractiveElements() {
    // Add ripple effect to buttons
    document.querySelectorAll('button').forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
    
    // Add hover states to cards
    document.querySelectorAll('.modern-card, .stat-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

/**
 * Initialize tooltip functionality
 */
function initTooltips() {
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        const tooltipText = element.getAttribute('data-tooltip');
        
        const tooltip = document.createElement('span');
        tooltip.classList.add('tooltiptext');
        tooltip.textContent = tooltipText;
        
        element.classList.add('tooltip');
        element.appendChild(tooltip);
    });
}

/**
 * Flash element with success or error color
 */
function flashElement(element, type = 'success') {
    const className = type === 'success' ? 'flash-success' : 'flash-error';
    element.classList.add(className);
    setTimeout(() => element.classList.remove(className), 500);
}

/**
 * Show loading skeleton for async content
 */
function showSkeleton(container) {
    container.classList.add('skeleton');
    container.innerHTML = '<div style="height: 100%; width: 100%;"></div>';
}

/**
 * Hide loading skeleton
 */
function hideSkeleton(container, content) {
    container.classList.remove('skeleton');
    container.innerHTML = content;
}

/**
 * Smooth scroll to element
 */
function smoothScrollTo(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

/**
 * Add glow effect to element temporarily
 */
function temporaryGlow(element, duration = 2000) {
    element.classList.add('glow');
    setTimeout(() => element.classList.remove('glow'), duration);
}

/**
 * Create and show toast notification
 */
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} fade-in`;
    toast.textContent = message;
    
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        box-shadow: var(--shadow-md);
        z-index: 10000;
        max-width: 300px;
    `;
    
    // Add color based on type
    if (type === 'success') {
        toast.style.borderLeftColor = 'var(--success-color)';
        toast.style.borderLeftWidth = '4px';
    } else if (type === 'error') {
        toast.style.borderLeftColor = 'var(--danger-color)';
        toast.style.borderLeftWidth = '4px';
    } else if (type === 'warning') {
        toast.style.borderLeftColor = 'var(--warning-color)';
        toast.style.borderLeftWidth = '4px';
    }
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Enhance chart appearance with custom styling
 */
function enhanceChart(chartElement) {
    if (!chartElement) return;
    
    chartElement.classList.add('chart-container', 'scale-up');
    
    // Add loading state
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-shimmer';
    loadingOverlay.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border-radius: 12px;
        pointer-events: none;
    `;
    
    chartElement.style.position = 'relative';
    chartElement.appendChild(loadingOverlay);
    
    // Remove loading after chart renders
    setTimeout(() => {
        loadingOverlay.remove();
    }, 1000);
}

/**
 * Format numbers with commas and appropriate decimals
 */
function formatNumber(num, decimals = 2) {
    return num.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Format currency values
 */
function formatCurrency(amount, decimals = 2) {
    return '$' + formatNumber(amount, decimals);
}

/**
 * Format percentage values
 */
function formatPercentage(value, decimals = 1) {
    return formatNumber(value, decimals) + '%';
}

/**
 * Add pulsing animation to status indicators
 */
function pulseStatus(statusElement) {
    statusElement.classList.add('pulse');
}

/**
 * Detect dark mode preference
 */
function detectDarkMode() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

/**
 * Export utility functions for use in Dash callbacks
 */
window.MarketPie5UI = {
    flashElement,
    showSkeleton,
    hideSkeleton,
    smoothScrollTo,
    temporaryGlow,
    showToast,
    enhanceChart,
    formatNumber,
    formatCurrency,
    formatPercentage,
    pulseStatus,
    detectDarkMode
};

// Add CSS for ripple effect
const style = document.createElement('style');
style.textContent = `
    button {
        position: relative;
        overflow: hidden;
    }
    
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
