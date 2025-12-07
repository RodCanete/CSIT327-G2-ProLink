// ProLink Dashboard - Web Application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all dashboard functionality
    initMetricsCounter();
    initUserMenu();
    initNotifications();
    initActionItems();
    initActivityFeed();
    initResponsiveFeatures();
    initRequestsPage();
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
        notificationIcon.addEventListener('click', function(e) {
            e.stopPropagation();
            showNotificationDropdown();
        });
    }
    
    // Update notification badge on load
    updateNotificationBadge();
    
    // Poll for new notifications every 30 seconds
    setInterval(() => {
        updateNotificationBadge();
    }, 30000);
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
    if (!badge) return;
    
    // Fetch real notification count from API
    fetch('/notifications/api/count/')
        .then(response => response.json())
        .then(data => {
            const count = data.unread_count || 0;
            badge.textContent = count;
            badge.style.display = count > 0 ? 'block' : 'none';
        })
        .catch(error => {
            console.error('Error fetching notification count:', error);
            // Hide badge on error
            badge.style.display = 'none';
        });
}

function showNotificationDropdown() {
    // Remove existing dropdown if any
    const existingDropdown = document.querySelector('.notification-dropdown');
    if (existingDropdown) {
        existingDropdown.remove();
        return;
    }
    
    // Create dropdown
    const dropdown = document.createElement('div');
    dropdown.className = 'notification-dropdown';
    dropdown.innerHTML = `
        <div class="notification-header">
            <h4>Notifications</h4>
            <button class="mark-all-read">Mark all read</button>
        </div>
        <div class="notification-list">
            <div class="notification-loading">Loading notifications...</div>
        </div>
    `;
    
    // Style the dropdown
    dropdown.style.cssText = `
        position: absolute;
        top: 100%;
        right: 0;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.05);
        width: 400px;
        max-height: 500px;
        overflow: hidden;
        z-index: 1000;
        animation: fadeInDown 0.2s ease-out;
        border: 1px solid var(--gray-200);
    `;
    
    // Position relative to notifications icon
    const notifications = document.querySelector('.notifications');
    notifications.style.position = 'relative';
    notifications.appendChild(dropdown);
    
    // Fetch real notifications
    fetch('/notifications/api/list/?limit=20')
        .then(response => response.json())
        .then(data => {
            const notificationList = dropdown.querySelector('.notification-list');
            notificationList.innerHTML = '';
            
            if (data.notifications && data.notifications.length > 0) {
                data.notifications.forEach(notif => {
                    const notificationItem = document.createElement('div');
                    notificationItem.className = `notification-item ${notif.is_read ? '' : 'unread'}`;
                    notificationItem.dataset.notificationId = notif.id;
                    
                    // Build notification content with details
                    let notificationDetails = '';
                    if (notif.from_user) {
                        notificationDetails += `<span class="notification-from">From: ${notif.from_user}</span>`;
                    }
                    if (notif.request_title) {
                        if (notificationDetails) notificationDetails += ' • ';
                        notificationDetails += `<span class="notification-request">${notif.request_title}</span>`;
                    }
                    
                    notificationItem.innerHTML = `
                        <div class="notification-icon">
                            <i class="fas ${notif.icon}"></i>
                        </div>
                        <div class="notification-content">
                            <p class="notification-title">${notif.title}</p>
                            ${notificationDetails ? `<div class="notification-details">${notificationDetails}</div>` : ''}
                            <div class="notification-time">${notif.time_ago}</div>
                        </div>
                    `;
                    
                    // Add click handler to mark as read and navigate
                    notificationItem.addEventListener('click', function() {
                        if (!notif.is_read) {
                            markNotificationAsRead(notif.id);
                            notificationItem.classList.remove('unread');
                        }
                        if (notif.link_url) {
                            window.location.href = notif.link_url;
                        }
                    });
                    
                    notificationList.appendChild(notificationItem);
                });
            } else {
                notificationList.innerHTML = '<div class="notification-empty">No notifications</div>';
            }
        })
        .catch(error => {
            console.error('Error fetching notifications:', error);
            const notificationList = dropdown.querySelector('.notification-list');
            notificationList.innerHTML = '<div class="notification-error">Error loading notifications</div>';
        });
    
    // Mark all as read button
    const markAllReadBtn = dropdown.querySelector('.mark-all-read');
    markAllReadBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        markAllNotificationsAsRead();
    });
    
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

function markNotificationAsRead(notificationId) {
    fetch(`/notifications/api/${notificationId}/read/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update badge count
            updateNotificationBadge();
        }
    })
    .catch(error => console.error('Error marking notification as read:', error));
}

function markAllNotificationsAsRead() {
    fetch('/notifications/api/mark-all-read/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update badge count
            updateNotificationBadge();
            // Reload dropdown
            const dropdown = document.querySelector('.notification-dropdown');
            if (dropdown) {
                dropdown.remove();
                showNotificationDropdown();
            }
        }
    })
    .catch(error => console.error('Error marking all notifications as read:', error));
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
        padding: 1rem 1.25rem;
        border-bottom: 1px solid var(--gray-200);
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: var(--white);
        position: sticky;
        top: 0;
        z-index: 10;
    }
    
    .notification-header h4 {
        margin: 0;
        font-size: 0.9375rem;
        font-weight: 600;
        color: var(--gray-900);
        text-align: left;
    }
    
    .mark-all-read {
        background: none;
        border: none;
        color: var(--primary-color);
        font-size: 0.8125rem;
        cursor: pointer;
        font-weight: 500;
        padding: 0.375rem 0.625rem;
        border-radius: 4px;
        transition: background-color 0.15s ease;
        text-align: right;
    }
    
    .mark-all-read:hover {
        background: var(--gray-100);
    }
    
    .notification-list {
        max-height: 450px;
        overflow-y: auto;
        background: var(--white);
    }
    
    .notification-list::-webkit-scrollbar {
        width: 6px;
    }
    
    .notification-list::-webkit-scrollbar-track {
        background: transparent;
    }
    
    .notification-list::-webkit-scrollbar-thumb {
        background: var(--gray-300);
        border-radius: 3px;
    }
    
    .notification-list::-webkit-scrollbar-thumb:hover {
        background: var(--gray-400);
    }
    
    .notification-item {
        padding: 0.875rem 1.25rem;
        border-bottom: 1px solid var(--gray-200);
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        cursor: pointer;
        transition: background-color 0.15s ease;
        position: relative;
    }
    
    .notification-item:hover {
        background: var(--gray-50);
    }
    
    .notification-item:last-child {
        border-bottom: none;
    }
    
    .notification-icon {
        width: 36px;
        height: 36px;
        min-width: 36px;
        border-radius: 8px;
        background: var(--gray-100);
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--gray-700);
        font-size: 0.875rem;
        flex-shrink: 0;
    }
    
    .notification-content {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        text-align: left;
    }
    
    .notification-title {
        margin: 0;
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--gray-900);
        line-height: 1.4;
        text-align: left;
    }
    
    .notification-details {
        font-size: 0.8125rem;
        color: var(--gray-600);
        line-height: 1.4;
        text-align: left;
        margin-top: 0.125rem;
    }
    
    .notification-from {
        font-weight: 400;
    }
    
    .notification-request {
        color: var(--primary-color);
        font-weight: 500;
    }
    
    .notification-time {
        font-size: 0.75rem;
        color: var(--gray-500);
        margin-top: 0.25rem;
        text-align: left;
    }
    
    .notification-item.unread {
        background: #f0f9ff;
    }
    
    .notification-item.unread::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 3px;
        background: var(--primary-color);
    }
    
    .notification-item.unread .notification-title {
        font-weight: 600;
        color: var(--gray-900);
    }
    
    .notification-item.unread .notification-icon {
        background: var(--primary-color);
        color: white;
    }
    
    .notification-loading,
    .notification-empty,
    .notification-error {
        padding: 2rem 1.25rem;
        text-align: left;
        color: var(--gray-500);
        font-size: 0.875rem;
    }
    
    .notification-error {
        color: var(--danger-color);
    }
`;
document.head.appendChild(style);

// Requests page functionality
function initRequestsPage() {
    // Only initialize if we're on the requests page
    if (!document.querySelector('.requests-grid')) {
        return;
    }
    
    initRequestFilters();
    initRequestSearch();
    initRequestModals();
    initRequestActions();
}

// Filter functionality for requests
function initRequestFilters() {
    const filterTabs = document.querySelectorAll('.filter-tab');
    
    filterTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const status = this.dataset.status;
            const url = new URL(window.location);
            url.searchParams.set('status', status);
            window.location.href = url.toString();
        });
    });
}

// Search functionality for requests
function initRequestSearch() {
    const searchInput = document.getElementById('searchInput');
    
    if (searchInput) {
        // Only search when Enter key is pressed
        searchInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                const searchQuery = this.value.trim();
                const url = new URL(window.location);
                
                if (searchQuery) {
                    url.searchParams.set('search', searchQuery);
                } else {
                    url.searchParams.delete('search');
                }
                
                window.location.href = url.toString();
            }
        });
    }
}

// Modal functionality for requests
function initRequestModals() {
    // Request detail modal
    const requestDetailModal = document.getElementById('requestDetailModal');
    const messageModal = document.getElementById('messageModal');
    
    // Close modals when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === requestDetailModal) {
            closeRequestModal();
        }
        if (event.target === messageModal) {
            closeMessageModal();
        }
    });
    
    // Close modals with escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeRequestModal();
            closeMessageModal();
        }
    });
}

// Request action handlers
function initRequestActions() {
    // These functions are defined in the template but we can enhance them here
    window.viewRequestDetails = function(requestId) {
        // Load detailed request information
        const modal = document.getElementById('requestDetailModal');
        const modalContent = document.getElementById('modalContent');
        
        // For now, show sample content
        modalContent.innerHTML = `
            <div class="request-detail">
                <h3>Request #${requestId}</h3>
                <p>Detailed request information would be loaded here...</p>
                <div class="request-timeline">
                    <h4>Timeline</h4>
                    <div class="timeline-item">
                        <span class="timeline-date">2024-01-15</span>
                        <span class="timeline-action">Request created</span>
                    </div>
                    <div class="timeline-item">
                        <span class="timeline-date">2024-01-16</span>
                        <span class="timeline-action">Professional assigned</span>
                    </div>
                </div>
            </div>
        `;
        
        modal.style.display = 'block';

        const copyBtn = document.getElementById('copyRequestId');
    copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(requestId)
            .then(() => alert(`Request ID #${requestId} copied to clipboard!`))
            .catch(err => console.error('Failed to copy: ', err));
    });
    };
    
    window.closeRequestModal = function() {
        document.getElementById('requestDetailModal').style.display = 'none';
    };
    
    window.openMessageModal = function(requestId) {
        const modal = document.getElementById('messageModal');
        const messageThread = document.getElementById('messageThread');
        
        // Load message thread
        messageThread.innerHTML = `
            <div class="message-item">
                <div class="message-header">
                    <span class="message-sender">You</span>
                    <span class="message-time">2 hours ago</span>
                </div>
                <div class="message-content">Hello, I have a question about my request...</div>
            </div>
            <div class="message-item">
                <div class="message-header">
                    <span class="message-sender">Dr. Sarah Johnson</span>
                    <span class="message-time">1 hour ago</span>
                </div>
                <div class="message-content">Hi! I'm working on your request and will have it ready by tomorrow.</div>
            </div>
        `;
        
        modal.style.display = 'block';
    };
    
    window.closeMessageModal = function() {
        document.getElementById('messageModal').style.display = 'none';
    };
    
    window.sendMessage = function() {
        const messageText = document.getElementById('messageText');
        const message = messageText.value.trim();
        
        if (message) {
            // Add message to thread
            const messageThread = document.getElementById('messageThread');
            const now = new Date().toLocaleTimeString();
            
            const messageElement = document.createElement('div');
            messageElement.className = 'message-item';
            messageElement.innerHTML = `
                <div class="message-header">
                    <span class="message-sender">You</span>
                    <span class="message-time">${now}</span>
                </div>
                <div class="message-content">${message}</div>
            `;
            
            messageThread.appendChild(messageElement);
            messageText.value = '';
            
            // Scroll to bottom
            messageThread.scrollTop = messageThread.scrollHeight;
            
            // In a real implementation, send to server
            console.log('Sending message:', message);
        }
    };
    
    window.cancelRequest = function(requestId) {
        if (confirm('Are you sure you want to cancel this request? This action cannot be undone.')) {
            // In a real implementation, send cancellation request to server
            fetch(`/requests/${requestId}/cancel/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Reload page to show updated status
                    window.location.reload();
                } else {
                    alert('Error cancelling request: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error cancelling request. Please try again.');
            });
        }
    };
    
    window.createNewRequest = function() {
        // Redirect to create request page or show modal
        window.location.href = '/requests/create/';
    };
}

// Utility function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Modal functionality for client requests
let currentRequestId = null;

function showAcceptModal(requestId, price) {
    currentRequestId = requestId;
    document.getElementById('acceptPrice').textContent = price;
    document.getElementById('acceptModal').classList.add('active');
}

function hideAcceptModal() {
    document.getElementById('acceptModal').classList.remove('active');
    currentRequestId = null;
}

function showDeclineModal(requestId) {
    currentRequestId = requestId;
    document.getElementById('declineModal').classList.add('active');
}

function hideDeclineModal() {
    document.getElementById('declineModal').classList.remove('active');
    currentRequestId = null;
}

function submitAcceptForm() {
    if (currentRequestId) {
        document.getElementById('accept-form-' + currentRequestId).submit();
    }
}

function submitDeclineForm() {
    if (currentRequestId) {
        document.getElementById('decline-form-' + currentRequestId).submit();
    }
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        hideAcceptModal();
        hideDeclineModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        hideAcceptModal();
        hideDeclineModal();
    }
});