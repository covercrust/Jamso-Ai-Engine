// Jamso AI Dashboard Scripts
console.log("Script.js is loaded!");

// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded");
    
    // Initialize dashboard components
    initializeDashboard();
    
    // Set up event listeners
    setupEventListeners();
});

/**
 * Initialize dashboard components
 */
function initializeDashboard() {
    // Check if we're on the dashboard page
    if (document.querySelector('.dashboard-container')) {
        console.log("Dashboard page detected, initializing components");
        
        // Initialize charts if they exist
        initializeCharts();
        
        // Load account data
        loadAccountData();
        
        // Check for notifications
        checkNotifications();
    }
}

/**
 * Set up event listeners for interactive elements
 */
function setupEventListeners() {
    // Account selector
    const accountSelector = document.getElementById('account-selector');
    if (accountSelector) {
        accountSelector.addEventListener('change', function() {
            console.log("Account changed to:", this.value);
            // Reload dashboard data with new account
            loadAccountData(this.value);
        });
    }
    
    // Refresh button
    const refreshBtn = document.getElementById('refresh-data');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            console.log("Manual refresh requested");
            loadAccountData();
        });
    }
    
    // Trade form submission
    const tradeForm = document.getElementById('trade-form');
    if (tradeForm) {
        tradeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitTradeForm(this);
        });
    }
}

/**
 * Initialize dashboard charts
 */
function initializeCharts() {
    console.log("Initializing dashboard charts");
    // This would typically use a charting library like Chart.js
    // For now, this is just a placeholder
}

/**
 * Load account data from API
 * @param {string} accountId - Optional account ID to load
 */
function loadAccountData(accountId = null) {
    console.log("Loading account data");
    
    // API endpoint
    let endpoint = '/api/accounts';
    if (accountId) {
        endpoint += `?account_id=${accountId}`;
    }
    
    // Fetch data
    fetch(endpoint)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log("Account data loaded:", data);
            updateDashboardUI(data);
        })
        .catch(error => {
            console.error("Error loading account data:", error);
            showNotification('error', 'Failed to load account data');
        });
}

/**
 * Update dashboard UI with account data
 * @param {Object} data - Account data
 */
function updateDashboardUI(data) {
    // This would update various dashboard elements with the account data
    console.log("Updating dashboard UI with data");
}

/**
 * Show notification message
 * @param {string} type - Notification type (success, error, warning)
 * @param {string} message - Notification message
 */
function showNotification(type, message) {
    console.log(`${type.toUpperCase()} notification:`, message);
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.textContent = message;
    
    // Add to notifications area
    const notificationsArea = document.getElementById('notifications');
    if (notificationsArea) {
        notificationsArea.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

/**
 * Check for system notifications
 */
function checkNotifications() {
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            if (data.notifications && data.notifications.length > 0) {
                data.notifications.forEach(notification => {
                    showNotification(notification.type, notification.message);
                });
            }
        })
        .catch(error => {
            console.error("Error checking notifications:", error);
        });
}

/**
 * Submit trade form
 * @param {HTMLFormElement} form - Trade form element
 */
function submitTradeForm(form) {
    const formData = new FormData(form);
    const tradeData = {};
    
    // Convert FormData to object
    for (let [key, value] of formData.entries()) {
        tradeData[key] = value;
    }
    
    console.log("Submitting trade:", tradeData);
    
    // Send to API
    fetch('/api/trade', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(tradeData),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('success', 'Trade executed successfully!');
            form.reset();
        } else {
            showNotification('error', `Trade failed: ${data.message}`);
        }
    })
    .catch(error => {
        console.error("Error submitting trade:", error);
        showNotification('error', 'Failed to submit trade');
    });
}
