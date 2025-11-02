// Professionals List JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize save/bookmark functionality
    initSaveButtons();
    
    // Auto-submit filters on change
    initAutoSubmitFilters();
});

// Save/Bookmark Professional
function initSaveButtons() {
    const saveButtons = document.querySelectorAll('.save-btn');
    
    saveButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const professionalId = this.dataset.professionalId;
            const isSaved = this.classList.contains('saved');
            
            // Toggle saved state immediately for better UX
            toggleSaveButton(this, !isSaved);
            
            // Send AJAX request to save/unsave
            fetch(`/professionals/${professionalId}/${isSaved ? 'unsave' : 'save'}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    showNotification(
                        isSaved ? 'Professional removed from saved list' : 'Professional saved successfully',
                        'success'
                    );
                } else {
                    // Revert if failed
                    toggleSaveButton(this, isSaved);
                    showNotification(data.message || 'Action failed. Please try again.', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // Revert on error
                toggleSaveButton(this, isSaved);
                showNotification('An error occurred. Please try again.', 'error');
            });
        });
    });
}

function toggleSaveButton(button, saved) {
    if (saved) {
        button.classList.add('saved');
        button.querySelector('i').classList.remove('far');
        button.querySelector('i').classList.add('fas');
        button.title = 'Remove from saved';
    } else {
        button.classList.remove('saved');
        button.querySelector('i').classList.remove('fas');
        button.querySelector('i').classList.add('far');
        button.title = 'Save for later';
    }
}

// Auto-submit filters
function initAutoSubmitFilters() {
    const form = document.querySelector('.search-filter-form');
    const selects = form.querySelectorAll('select');
    
    selects.forEach(select => {
        select.addEventListener('change', function() {
            // Optional: Add a small delay for better UX
            setTimeout(() => {
                form.submit();
            }, 300);
        });
    });
}

// Get CSRF token from cookie
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

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#007bff'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        display: flex;
        align-items: center;
        gap: 0.75rem;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
