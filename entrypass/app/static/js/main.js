/**
 * Main JavaScript File
 * =====================
 * 
 * Event Ticketing System - Main JavaScript
 */

// =====================
// Utility Functions
// =====================

/**
 * Auto-dismiss flash messages after delay
 */
function dismissFlashMessages() {
    const messages = document.querySelectorAll('.flash');
    messages.forEach(function(msg) {
        setTimeout(function() {
            msg.style.opacity = '0';
            setTimeout(function() {
                msg.remove();
            }, 300);
        }, 5000);
    });
}

/**
 * Show a notification message
 */
function showNotification(message, type) {
    type = type || 'info';
    const container = document.querySelector('.flash-messages');
    if (container) {
        const div = document.createElement('div');
        div.className = 'flash ' + type;
        div.textContent = message;
        container.appendChild(div);
        dismissFlashMessages();
    }
}

// =====================
// Form Validation
// =====================

/**
 * Validate required form fields
 */
function validateForm(form) {
    const required = form.querySelectorAll('[required]');
    let valid = true;
    required.forEach(function(field) {
        if (!field.value.trim()) {
            field.style.borderColor = '#dc3545';
            valid = false;
        } else {
            field.style.borderColor = '#ddd';
        }
    });
    return valid;
}

// =====================
// API Helpers
// =====================

/**
 * Make an API request
 */
function apiRequest(url, method, data) {
    method = method || 'GET';
    return fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: data ? JSON.stringify(data) : undefined
    }).then(function(response) {
        return response.json();
    });
}

// =====================
// Event Listeners
// =====================

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages
    dismissFlashMessages();
    
    // Add form validation to all forms
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });
    });
    
    console.log('Event Ticketing System initialized');
});
