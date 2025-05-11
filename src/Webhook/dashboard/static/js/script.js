// Dashboard functionality for Jamso AI Server

console.log("Script.js is loaded!");

document.addEventListener('DOMContentLoaded', function() {
    // Initialize event handlers
    initializeEventHandlers();
    
    // Fetch initial data
    fetchPositions();
    fetchAccountInfo();
    
    // Set up periodic data refresh
    setInterval(fetchPositions, 30000); // Refresh every 30 seconds
    setInterval(fetchAccountInfo, 60000); // Refresh account info every minute
});

function initializeEventHandlers() {
    // Add event listeners to buttons and forms
    const closePositionButtons = document.querySelectorAll('.close-position-button');
    closePositionButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            const positionId = this.getAttribute('data-position-id');
            closePosition(positionId);
        });
    });
    
    // Trade form submission
    const tradeForm = document.getElementById('trade-form');
    if (tradeForm) {
        tradeForm.addEventListener('submit', function(event) {
            event.preventDefault();
            submitTradeForm(this);
        });
    }
    
    // Toggle sections
    const toggleButtons = document.querySelectorAll('.toggle-section');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.classList.toggle('hidden');
                // Update button text based on visibility
                this.textContent = targetElement.classList.contains('hidden') 
                    ? 'Show ' + this.getAttribute('data-section-name')
                    : 'Hide ' + this.getAttribute('data-section-name');
            }
        });
    });
}

function fetchPositions() {
    fetch('/api/positions')
        .then(response => response.json())
        .then(data => {
            updatePositionsTable(data);
        })
        .catch(error => {
            console.error('Error fetching positions:', error);
            showNotification('Failed to fetch positions data', 'error');
        });
}

function fetchAccountInfo() {
    fetch('/api/accounts')
        .then(response => response.json())
        .then(data => {
            updateAccountInfo(data);
        })
        .catch(error => {
            console.error('Error fetching account info:', error);
            showNotification('Failed to fetch account information', 'error');
        });
}

function updatePositionsTable(positions) {
    const tableBody = document.querySelector('#positions-table tbody');
    if (!tableBody) return;
    
    // Clear current rows
    tableBody.innerHTML = '';
    
    if (positions.length === 0) {
        // No positions
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = '<td colspan="7" class="text-center">No open positions</td>';
        tableBody.appendChild(emptyRow);
        return;
    }
    
    // Add positions to table
    positions.forEach(position => {
        const row = document.createElement('tr');
        
        // Format profit/loss with color
        const profitLossClass = parseFloat(position.profitLoss) >= 0 ? 'text-success' : 'text-danger';
        
        row.innerHTML = `
            <td>${position.id}</td>
            <td>${position.symbol}</td>
            <td>${position.direction}</td>
            <td>${position.size}</td>
            <td>${position.entryPrice}</td>
            <td>${position.currentPrice}</td>
            <td class="${profitLossClass}">${position.profitLoss}</td>
            <td>
                <button class="close-position-button" data-position-id="${position.id}">Close</button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Re-attach event listeners
    const closeButtons = tableBody.querySelectorAll('.close-position-button');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const positionId = this.getAttribute('data-position-id');
            closePosition(positionId);
        });
    });
}

function updateAccountInfo(accountData) {
    // Update account information display
    const account = accountData[0]; // Assuming first account is used
    if (!account) return;
    
    const balanceElement = document.getElementById('account-balance');
    if (balanceElement) {
        balanceElement.textContent = `${account.balance} ${account.currency}`;
    }
    
    const accountNameElement = document.getElementById('account-name');
    if (accountNameElement) {
        accountNameElement.textContent = account.name;
    }
}

function submitTradeForm(form) {
    const formData = new FormData(form);
    const tradeData = Object.fromEntries(formData.entries());
    
    // Show loading state
    form.querySelector('button[type="submit"]').disabled = true;
    
    fetch('/webhook', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Trading-Token': tradeData.token
        },
        body: JSON.stringify({
            order_id: generateOrderId(),
            ticker: tradeData.symbol,
            order_action: tradeData.direction,
            position_size: tradeData.size,
            price: tradeData.price || null,
            stop_loss: tradeData.stopLoss || null,
            take_profit: tradeData.takeProfit || null
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('Trade executed successfully', 'success');
            form.reset();
            // Refresh positions table
            fetchPositions();
        } else {
            showNotification(`Trade failed: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error executing trade:', error);
        showNotification('Error submitting trade request', 'error');
    })
    .finally(() => {
        // Re-enable button
        form.querySelector('button[type="submit"]').disabled = false;
    });
}

function closePosition(positionId) {
    if (!confirm('Are you sure you want to close this position?')) {
        return;
    }
    
    fetch('/close_position', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            order_id: positionId,
            size: 'all' // Close entire position
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('Position closed successfully', 'success');
            // Refresh positions
            fetchPositions();
        } else {
            showNotification(`Failed to close position: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error closing position:', error);
        showNotification('Error closing position', 'error');
    });
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type}`;
    notification.textContent = message;
    
    // Add to notifications area
    const notificationsArea = document.getElementById('notifications-area');
    if (notificationsArea) {
        notificationsArea.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    } else {
        // Fallback to alert if notifications area not found
        alert(`${type.toUpperCase()}: ${message}`);
    }
}

function generateOrderId() {
    // Generate a unique order ID combining timestamp and random string
    const timestamp = new Date().getTime();
    const randomStr = Math.random().toString(36).substring(2, 10);
    return `order_${timestamp}_${randomStr}`;
}
