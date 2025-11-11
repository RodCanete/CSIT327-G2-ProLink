/**
 * ProLink Messaging System
 * Handles real-time messaging functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    initUnreadBadgePolling();
});

/**
 * Poll for unread message count and update navbar badge
 * Runs every 30 seconds
 */
function initUnreadBadgePolling() {
    const badge = document.getElementById('unreadMessagesBadge');
    
    if (!badge) {
        console.warn('Unread messages badge element not found');
        return;
    }

    // Function to update badge
    async function updateUnreadBadge() {
        try {
            const response = await fetch('/messages/api/unread-count/');
            const data = await response.json();
            
            if (data.unread_count > 0) {
                badge.textContent = data.unread_count > 99 ? '99+' : data.unread_count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        } catch (error) {
            console.error('Error fetching unread count:', error);
        }
    }

    // Initial update
    updateUnreadBadge();
    
    // Poll every 30 seconds
    setInterval(updateUnreadBadge, 30000);
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
}

/**
 * Show notification banner
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Fade in
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
