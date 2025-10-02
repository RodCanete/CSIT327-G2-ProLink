// ProLink Dashboard - Web Application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all dashboard functionality
    initMetricsCounter();
    initUserMenu();
    initNotifications();
    initActionItems();
    initActivityFeed();
    initResponsiveFeatures();
});

// Animated counter for metrics
function initMetricsCounter() {
    const metricNumbers = document.querySelectorAll('.metric-number');
    
    const animateCounter = (element) => {
        const target = parseInt(element.getAttribute('data-target'));
        const duration = 2000; // 2 seconds
        const increment = target / (duration / 16); // 60fps
        let current = 0;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current);
        }, 16);
    };
    
    // Intersection Observer to trigger animation when metrics come into view
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    metricNumbers.forEach(metric => {
        observer.observe(metric);
    });
}

// User menu functionality
function initUserMenu() {
    const userInfo = document.querySelector('.user-info');
    const userDropdown = document.querySelector('.user-dropdown');
    
    if (userInfo && userDropdown) {
        let isOpen = false;
        
        userInfo.addEventListener('click', function(e) {
            e.stopPropagation();
            isOpen = !isOpen;
            userDropdown.style.display = isOpen ? 'block' : 'none';
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!userInfo.contains(e.target) && !userDropdown.contains(e.target)) {
                isOpen = false;
                userDropdown.style.display = 'none';
            }
        });
        
        // Close dropdown on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                isOpen = false;
                userDropdown.style.display = 'none';
            }
        });
    }
}

// Notification system
function initNotifications() {
    const notificationIcon = document.querySelector('.notifications');
    const notificationBadge = document.querySelector('.notification-badge');
    
    if (notificationIcon) {
        notificationIcon.addEventListener('click', function() {
            showNotificationDropdown();
        });
    }
    
    // Simulate real-time notifications
    setInterval(() => {
        updateNotificationBadge();
    }, 30000); // Check every 30 seconds
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close">&times;</button>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 1rem;
        min-width: 300px;
        animation: slideInRight 0.3s ease-out;
        border-left: 4px solid ${getNotificationColor(type)};
    `;
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
    
    // Close button functionality
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        notification.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    });
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function getNotificationColor(type) {
    const colors = {
        'success': '#10b981',
        'error': '#ef4444',
        'warning': '#f59e0b',
        'info': '#06b6d4'
    };
    return colors[type] || '#06b6d4';
}

function updateNotificationBadge() {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        // Simulate random notification count
        const count = Math.floor(Math.random() * 5);
        badge.textContent = count;
        badge.style.display = count > 0 ? 'block' : 'none';
    }
}

function showNotificationDropdown() {
    // Create dropdown
    const dropdown = document.createElement('div');
    dropdown.className = 'notification-dropdown';
    dropdown.innerHTML = `
        <div class="notification-header">
            <h4>Notifications</h4>
            <button class="mark-all-read">Mark all read</button>
        </div>
        <div class="notification-list">
            <div class="notification-item">
                <div class="notification-icon">
                    <i class="fas fa-check-circle"></i>
                </div>
                <div class="notification-content">
                    <p>Validation completed for "Web Design Project"</p>
                    <span class="notification-time">2 hours ago</span>
                </div>
            </div>
            <div class="notification-item">
                <div class="notification-icon">
                    <i class="fas fa-user-plus"></i>
                </div>
                <div class="notification-content">
                    <p>New connection request from Sarah Johnson</p>
                    <span class="notification-time">4 hours ago</span>
                </div>
            </div>
            <div class="notification-item">
                <div class="notification-icon">
                    <i class="fas fa-star"></i>
                </div>
                <div class="notification-content">
                    <p>You received a 5-star review!</p>
                    <span class="notification-time">1 day ago</span>
                </div>
            </div>
        </div>
    `;
    
    // Style the dropdown
    dropdown.style.cssText = `
        position: absolute;
        top: 100%;
        right: 0;
        background: white;
        border-radius: 8px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        width: 350px;
        max-height: 400px;
        overflow-y: auto;
        z-index: 1000;
        animation: fadeInDown 0.3s ease-out;
        border: 1px solid var(--gray-200);
    `;
    
    // Position relative to notifications icon
    const notifications = document.querySelector('.notifications');
    notifications.style.position = 'relative';
    notifications.appendChild(dropdown);
    
    // Close dropdown when clicking outside
    setTimeout(() => {
        document.addEventListener('click', function closeDropdown(e) {
            if (!dropdown.contains(e.target) && !notifications.contains(e.target)) {
                dropdown.remove();
                document.removeEventListener('click', closeDropdown);
            }
        });
    }, 100);
}

// Action items functionality
function initActionItems() {
    const actionItems = document.querySelectorAll('.action-item');
    
    actionItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Add loading state
            this.classList.add('loading');
            
            // Simulate navigation delay
            setTimeout(() => {
                this.classList.remove('loading');
                // In a real app, this would navigate to the URL
                console.log('Navigating to:', this.href);
            }, 500);
        });
        
        // Add hover effects
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(8px)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(4px)';
        });
    });
}

// Activity feed functionality
function initActivityFeed() {
    const activityItems = document.querySelectorAll('.activity-item');
    
    // Add click handlers for activity items
    activityItems.forEach(item => {
        item.addEventListener('click', function() {
            this.style.background = 'var(--gray-100)';
            setTimeout(() => {
                this.style.background = '';
            }, 200);
        });
    });
    
    // Simulate real-time activity updates
    setInterval(() => {
        updateActivityFeed();
    }, 60000); // Update every minute
}

function updateActivityFeed() {
    const activityList = document.querySelector('.activity-list');
    if (!activityList) return;
    
    const activities = [
        {
            icon: 'fas fa-check-circle',
            text: 'New validation request received',
            time: 'Just now',
            type: 'success'
        },
        {
            icon: 'fas fa-user-plus',
            text: 'Connection accepted by Mike Chen',
            time: '5 minutes ago',
            type: 'info'
        },
        {
            icon: 'fas fa-star',
            text: 'Review submitted for "Logo Design"',
            time: '10 minutes ago',
            type: 'warning'
        }
    ];
    
    // Randomly add new activity
    if (Math.random() < 0.3) { // 30% chance
        const activity = activities[Math.floor(Math.random() * activities.length)];
        addActivityItem(activity);
    }
}

function addActivityItem(activity) {
    const activityList = document.querySelector('.activity-list');
    const activityItem = document.createElement('div');
    activityItem.className = 'activity-item';
    activityItem.innerHTML = `
        <div class="activity-icon ${activity.type}">
            <i class="${activity.icon}"></i>
        </div>
        <div class="activity-content">
            <p><strong>${activity.text}</strong></p>
            <span class="activity-time">${activity.time}</span>
        </div>
    `;
    
    // Add animation
    activityItem.style.opacity = '0';
    activityItem.style.transform = 'translateY(-20px)';
    
    activityList.insertBefore(activityItem, activityList.firstChild);
    
    // Animate in
    setTimeout(() => {
        activityItem.style.transition = 'all 0.3s ease-out';
        activityItem.style.opacity = '1';
        activityItem.style.transform = 'translateY(0)';
    }, 100);
    
    // Remove old items if too many
    const items = activityList.querySelectorAll('.activity-item');
    if (items.length > 5) {
        const lastItem = items[items.length - 1];
        lastItem.style.transition = 'all 0.3s ease-out';
        lastItem.style.opacity = '0';
        lastItem.style.transform = 'translateY(20px)';
        setTimeout(() => {
            if (lastItem.parentNode) {
                lastItem.parentNode.removeChild(lastItem);
            }
        }, 300);
    }
}

// Responsive features
function initResponsiveFeatures() {
    // Handle window resize
    window.addEventListener('resize', debounce(function() {
        // Close any open dropdowns on mobile
        if (window.innerWidth < 768) {
            const dropdowns = document.querySelectorAll('.user-dropdown, .notification-dropdown');
            dropdowns.forEach(dropdown => {
                dropdown.style.display = 'none';
            });
        }
    }, 250));
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
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
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    @keyframes fadeInDown {
        from {
            transform: translateY(-10px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    .notification {
        font-family: 'Inter', sans-serif;
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .notification-close {
        background: none;
        border: none;
        font-size: 1.25rem;
        color: var(--gray-500);
        cursor: pointer;
        padding: 0;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .notification-close:hover {
        color: var(--gray-700);
    }
    
    .notification-dropdown {
        font-family: 'Inter', sans-serif;
    }
    
    .notification-header {
        padding: 1rem 1.5rem;
        border-bottom: 1px solid var(--gray-200);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .notification-header h4 {
        margin: 0;
        font-size: 1rem;
        font-weight: 600;
        color: var(--gray-800);
    }
    
    .mark-all-read {
        background: none;
        border: none;
        color: var(--primary-color);
        font-size: 0.875rem;
        cursor: pointer;
        font-weight: 500;
    }
    
    .notification-list {
        max-height: 300px;
        overflow-y: auto;
    }
    
    .notification-item {
        padding: 1rem 1.5rem;
        border-bottom: 1px solid var(--gray-100);
        display: flex;
        align-items: center;
        gap: 1rem;
        cursor: pointer;
        transition: background-color 0.2s ease;
    }
    
    .notification-item:hover {
        background: var(--gray-50);
    }
    
    .notification-item:last-child {
        border-bottom: none;
    }
    
    .notification-icon {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: var(--gray-100);
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--primary-color);
        font-size: 0.875rem;
    }
    
    .notification-content p {
        margin: 0 0 0.25rem 0;
        font-size: 0.875rem;
        color: var(--gray-700);
    }
    
    .notification-time {
        font-size: 0.75rem;
        color: var(--gray-500);
    }
`;
document.head.appendChild(style);