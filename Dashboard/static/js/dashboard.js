/**
 * Jamso AI Trading Bot - Dashboard JavaScript
 * Enhancements:
 * - Added detailed comments for better understanding.
 * - Optimized code for real-time performance and maintainability.
 */

// Initialize dashboard when DOM content is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all dashboard components
    initDashboard();

    // Setup automatic refresh intervals
    setupRefreshIntervals();
});

/**
 * Initialize all dashboard components.
 *
 * Purpose:
 * - Updates the current date and time.
 * - Prepares the dashboard for real-time data updates.
 */
function initDashboard() {
    console.log("Initializing dashboard components.");
    // Update current date and time
    updateDateTime();
    // Additional initialization logic here...
}

/**
 * Set up automatic refresh intervals for dashboard data
 */
function setupRefreshIntervals() {
    // Update time every second
    setInterval(updateDateTime, 1000);
    
    // Update system status every 30 seconds
    setInterval(updateSystemStatus, 30000);
    
    // Refresh trades data every 60 seconds
    setInterval(fetchRecentTrades, 60000);
}

/**
 * Set up all dashboard event listeners
 */
function setupEventListeners() {
    // Theme toggler
    const themeToggler = document.getElementById('themeToggler');
    if (themeToggler) {
        themeToggler.addEventListener('click', toggleTheme);
    }
    
    // Manual refresh buttons
    const refreshDataBtn = document.getElementById('refreshData');
    if (refreshDataBtn) {
        refreshDataBtn.addEventListener('click', function(e) {
            e.preventDefault();
            refreshAllDashboardData();
        });
    }
    
    // Trade history refresh button
    const refreshTradesBtn = document.getElementById('refreshTradeHistory');
    if (refreshTradesBtn) {
        refreshTradesBtn.addEventListener('click', function(e) {
            e.preventDefault();
            fetchRecentTrades();
        });
    }
    
    // Chart period buttons
    const chartBtns = document.querySelectorAll('.chart-period-btn');
    chartBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const period = this.dataset.period;
            updateChartPeriod(period);
            
            // Update active state
            chartBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Webhook form
    if (document.getElementById('webhookTesterForm')) {
        setupWebhookTester();
    }
}

/**
 * Update date and time display
 */
function updateDateTime() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = now.toLocaleString();
    }
}

/**
 * Load user's preferred theme
 */
function loadUserTheme() {
    const savedTheme = localStorage.getItem('dashboard_theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        
        const toggler = document.getElementById('themeToggler');
        if (toggler) {
            const icon = toggler.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-moon-o');
                icon.classList.add('fa-sun-o');
            }
            toggler.title = 'Switch to Light Mode';
        }
    }
}

/**
 * Toggle between light and dark theme
 */
function toggleTheme() {
    const body = document.body;
    const toggler = document.getElementById('themeToggler');
    
    if (!toggler) return;
    
    const icon = toggler.querySelector('i');
    
    if (body.classList.contains('dark-theme')) {
        // Switch to light theme
        body.classList.remove('dark-theme');
        if (icon) {
            icon.classList.remove('fa-sun-o');
            icon.classList.add('fa-moon-o');
        }
        toggler.title = 'Switch to Dark Mode';
        localStorage.setItem('dashboard_theme', 'light');
    } else {
        // Switch to dark theme
        body.classList.add('dark-theme');
        if (icon) {
            icon.classList.remove('fa-moon-o');
            icon.classList.add('fa-sun-o');
        }
        toggler.title = 'Switch to Light Mode';
        localStorage.setItem('dashboard_theme', 'dark');
    }
    
    // Save preference via API if user is logged in
    const userData = getUserData();
    if (userData && userData.id) {
        saveUserPreference('theme', body.classList.contains('dark-theme') ? 'dark' : 'light');
    }
}

/**
 * Get current user data from session
 */
function getUserData() {
    const userDataElement = document.getElementById('userData');
    if (userDataElement && userDataElement.dataset.user) {
        try {
            return JSON.parse(userDataElement.dataset.user);
        } catch (e) {
            console.error('Error parsing user data:', e);
        }
    }
    return null;
}

/**
 * Save a user preference via API
 */
function saveUserPreference(key, value) {
    // Get existing preferences
    const preferences = JSON.parse(localStorage.getItem('user_preferences') || '{}');
    
    // Update preference
    preferences[key] = value;
    
    // Save to localStorage
    localStorage.setItem('user_preferences', JSON.stringify(preferences));
    
    // Save to server
    fetch('/dashboard/api/save-preferences', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences),
    })
    .then(response => response.json())
    .catch(error => console.error('Error saving preferences:', error));
}

/**
 * Fetch recent trades data from API
 */
function fetchRecentTrades() {
    const tradeTable = document.getElementById('tradingHistoryTable');
    if (!tradeTable) return;
    
    const refreshBtn = document.getElementById('refreshTradeHistory');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Loading...';
    }
    
    // Fetch trades data from API
    fetch('/dashboard/api/trades?limit=10')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                updateTradesTable(data.data);
                
                // Update counts
                const activeCount = data.data.filter(trade => trade.status === 'Active').length;
                updateActiveTradesCount(activeCount);
                
                // Update last trade time
                if (data.data.length > 0) {
                    updateLastTradeTime(data.data[0].timestamp);
                }
            }
        })
        .catch(error => {
            console.error('Error fetching trades:', error);
        })
        .finally(() => {
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="fa fa-refresh"></i> Refresh';
            }
        });
}

/**
 * Update the trades table with new data
 */
function updateTradesTable(trades) {
    const tableBody = document.querySelector('#tradingHistoryTable tbody');
    if (!tableBody) return;
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    if (trades.length === 0) {
        // Show empty state
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = '<td colspan="8" class="text-center py-3">No trading activity found</td>';
        tableBody.appendChild(emptyRow);
        return;
    }
    
    // Add new rows
    trades.forEach(trade => {
        const row = document.createElement('tr');
        
        // Add classes based on action type
        if (trade.action.includes('BUY')) {
            row.classList.add('trade-row-buy');
        } else if (trade.action.includes('SELL')) {
            row.classList.add('trade-row-sell');
        }
        
        // Format timestamp
        let timestamp = trade.timestamp;
        try {
            const date = new Date(trade.timestamp);
            if (!isNaN(date)) {
                timestamp = date.toLocaleString();
            }
        } catch (e) {}
        
        row.innerHTML = `
            <td>${timestamp}</td>
            <td>${trade.symbol}</td>
            <td><span class="badge bg-${trade.action.includes('BUY') ? 'success' : 'danger'}">${trade.action}</span></td>
            <td>${trade.size}</td>
            <td>${typeof trade.price === 'number' ? trade.price.toFixed(2) : trade.price}</td>
            <td>${trade.stop_loss ? (typeof trade.stop_loss === 'number' ? trade.stop_loss.toFixed(2) : trade.stop_loss) : '-'}</td>
            <td>${trade.take_profit ? (typeof trade.take_profit === 'number' ? trade.take_profit.toFixed(2) : trade.take_profit) : '-'}</td>
            <td><span class="badge bg-${getStatusBadgeClass(trade.status)}">${trade.status}</span></td>
        `;
        
        tableBody.appendChild(row);
    });
}

/**
 * Get appropriate badge class for trade status
 */
function getStatusBadgeClass(status) {
    switch (status) {
        case 'Active': return 'warning';
        case 'Completed': return 'success';
        case 'Cancelled': return 'secondary';
        case 'Failed': return 'danger';
        default: return 'info';
    }
}

/**
 * Update active trades count
 */
function updateActiveTradesCount(count) {
    const countElement = document.getElementById('activeTradesCount');
    if (countElement) {
        countElement.textContent = count;
    }
}

/**
 * Update last trade time display
 */
function updateLastTradeTime(timestamp) {
    const timeElement = document.getElementById('lastTradeTime');
    if (!timeElement) return;
    
    try {
        const tradeTime = new Date(timestamp);
        const now = new Date();
        const diffSeconds = Math.floor((now - tradeTime) / 1000);
        
        if (diffSeconds < 60) {
            timeElement.textContent = 'Just now';
        } else if (diffSeconds < 3600) {
            const mins = Math.floor(diffSeconds / 60);
            timeElement.textContent = `${mins}m ago`;
        } else if (diffSeconds < 86400) {
            const hours = Math.floor(diffSeconds / 3600);
            timeElement.textContent = `${hours}h ago`;
        } else {
            const days = Math.floor(diffSeconds / 86400);
            timeElement.textContent = `${days}d ago`;
        }
    } catch (e) {
        timeElement.textContent = timestamp;
    }
}

/**
 * Initialize performance chart
 */
function initPerformanceChart() {
    const chartContainer = document.getElementById('tradingPerformanceChart');
    if (!chartContainer) return;
    
    // Fetch chart data
    fetch('/dashboard/api/performance')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                createPerformanceChart(data.data);
            }
        })
        .catch(error => {
            console.error('Error fetching performance data:', error);
        });
}

/**
 * Create performance chart with data
 */
function createPerformanceChart(chartData) {
    const chartContainer = document.getElementById('tradingPerformanceChart');
    if (!chartContainer) return;
    
    const ctx = chartContainer.getContext('2d');
    
    // Destroy existing chart if it exists
    if (window.performanceChart) {
        window.performanceChart.destroy();
    }
    
    // Create new chart
    window.performanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Account Balance',
                data: chartData.data,
                fill: true,
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
                pointRadius: 3,
                pointBackgroundColor: 'rgba(75, 192, 192, 1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `Balance: $${context.raw.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: false,
                    grid: {
                        color: 'rgba(200, 200, 200, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
}

/**
 * Update chart period
 */
function updateChartPeriod(period) {
    // Fetch chart data for the new period
    fetch(`/dashboard/api/performance?days=${period}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                updatePerformanceChart(data.data);
            }
        })
        .catch(error => {
            console.error('Error fetching performance data:', error);
        });
}

/**
 * Update existing performance chart with new data
 */
function updatePerformanceChart(chartData) {
    if (!window.performanceChart) return;
    
    window.performanceChart.data.labels = chartData.labels;
    window.performanceChart.data.datasets[0].data = chartData.data;
    window.performanceChart.update();
}

/**
 * Update system status indicators
 */
function updateSystemStatus() {
    fetch('/dashboard/api/system-status')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                updateStatusIndicators(data.data);
                updateStatusUpdateTime();
            }
        })
        .catch(error => {
            console.error('Error fetching system status:', error);
        });
}

/**
 * Update system status indicators with data
 */
function updateStatusIndicators(statusData) {
    // Update overall system status
    const systemStatusIndicator = document.querySelector('.system-status-indicator');
    if (systemStatusIndicator) {
        if (statusData.overall) {
            systemStatusIndicator.classList.remove('bg-warning', 'bg-danger');
            systemStatusIndicator.classList.add('bg-success');
            systemStatusIndicator.innerHTML = '<i class="fa fa-check"></i>';
        } else {
            systemStatusIndicator.classList.remove('bg-success', 'bg-warning');
            systemStatusIndicator.classList.add('bg-danger');
            systemStatusIndicator.innerHTML = '<i class="fa fa-times"></i>';
        }
    }
    
    // Update individual component status indicators
    const components = statusData.components;
    for (const [key, value] of Object.entries(components)) {
        const indicator = document.querySelector(`.status-${key}`);
        if (indicator) {
            indicator.classList.remove('bg-success', 'bg-warning', 'bg-danger');
            
            if (value === true) {
                indicator.classList.add('bg-success');
                indicator.innerHTML = '<i class="fa fa-check"></i>';
            } else {
                indicator.classList.add('bg-danger');
                indicator.innerHTML = '<i class="fa fa-times"></i>';
            }
        }
    }
}

/**
 * Update status last checked time
 */
function updateStatusUpdateTime() {
    const timeElement = document.getElementById('status-update-time');
    if (timeElement) {
        timeElement.textContent = 'Just now';
    }
}

/**
 * Webhook tester form setup
 */
function setupWebhookTester() {
    // Update JSON preview when form fields change
    const formInputs = document.querySelectorAll('#webhookTesterForm select, #webhookTesterForm input');
    formInputs.forEach(input => {
        input.addEventListener('change', updateJsonPreview);
    });
    
    // Update JSON button
    const updateJsonBtn = document.getElementById('updateJsonBtn');
    if (updateJsonBtn) {
        updateJsonBtn.addEventListener('click', updateJsonPreview);
    }
    
    // Send webhook button
    const sendWebhookBtn = document.getElementById('sendWebhookBtn');
    if (sendWebhookBtn) {
        sendWebhookBtn.addEventListener('click', sendTestWebhook);
    }
    
    // Initial JSON preview
    updateJsonPreview();
}

/**
 * Update webhook JSON preview
 */
function updateJsonPreview() {
    const form = document.getElementById('webhookTesterForm');
    if (!form) return;
    
    const symbol = document.getElementById('testSymbol').value;
    const action = document.getElementById('testAction').value;
    const size = parseFloat(document.getElementById('testSize').value) || 0.01;
    const stopLoss = document.getElementById('testStopLoss').value ? parseFloat(document.getElementById('testStopLoss').value) : null;
    const takeProfit = document.getElementById('testTakeProfit').value ? parseFloat(document.getElementById('testTakeProfit').value) : null;
    const trailingStop = document.getElementById('testTrailingStop').checked;
    
    const orderId = `manual_${new Date().getTime().toString().substring(7)}`;
    
    const webhookData = {
        order_id: orderId,
        ticker: symbol,
        order_action: action,
        market_price: getRandomPrice(symbol),
        position_size: size,
        stop_loss: stopLoss,
        take_profit: takeProfit,
        trailing_stop: trailingStop,
        timestamp: new Date().toISOString(),
        token: "6a87cf683ac94bc7f83bc09ba643dc578538d4eb46c931a60dc4fe3ec3c159cd"
    };
    
    const jsonPreview = document.getElementById('jsonPreview');
    if (jsonPreview) {
        jsonPreview.textContent = JSON.stringify(webhookData, null, 2);
    }
}

/**
 * Get random price based on symbol
 */
function getRandomPrice(symbol) {
    const prices = {
        'BTCUSD': 85100 + (Math.random() * 1000 - 500),
        'GOLD': 3468 + (Math.random() * 40 - 20),
        'EURUSD': 1.1488 + (Math.random() * 0.004 - 0.002),
        'USDJPY': 147.50 + (Math.random() * 0.3 - 0.15),
        'US500': 5450 + (Math.random() * 20 - 10),
        'GBPUSD': 1.3180 + (Math.random() * 0.004 - 0.002),
        'TSLA': 180 + (Math.random() * 4 - 2),
        'AAPL': 210 + (Math.random() * 3 - 1.5),
        'MSFT': 415 + (Math.random() * 5 - 2.5),
        'NVDA': 950 + (Math.random() * 10 - 5)
    };
    
    return parseFloat((prices[symbol] || 100).toFixed(2));
}

/**
 * Send test webhook
 */
function sendTestWebhook() {
    const jsonPreview = document.getElementById('jsonPreview');
    const responseArea = document.getElementById('webhookResponse');
    const responseData = document.getElementById('responseData');
    
    if (!jsonPreview || !responseArea || !responseData) return;
    
    // Show loading state
    responseArea.style.display = 'block';
    responseData.textContent = 'Sending webhook request...';
    
    try {
        const webhookData = JSON.parse(jsonPreview.textContent);
        
        fetch('/webhook', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(webhookData),
        })
        .then(response => response.json())
        .then(data => {
            responseData.textContent = JSON.stringify(data, null, 2);
            responseData.classList.remove('text-danger');
            
            // If successful, add to trade history
            if (data.success) {
                addTradeToHistory(webhookData);
            }
        })
        .catch(error => {
            responseData.textContent = JSON.stringify({
                success: false,
                error: 'Failed to send webhook: ' + error.message,
                timestamp: new Date().toISOString()
            }, null, 2);
            responseData.classList.add('text-danger');
        });
    } catch (e) {
        responseData.textContent = JSON.stringify({
            success: false,
            error: 'Invalid JSON data: ' + e.message,
            timestamp: new Date().toISOString()
        }, null, 2);
        responseData.classList.add('text-danger');
    }
}

/**
 * Add test trade to history table
 */
function addTradeToHistory(webhookData) {
    // Create trade object
    const trade = {
        timestamp: new Date().toISOString(),
        symbol: webhookData.ticker,
        action: webhookData.order_action,
        size: webhookData.position_size,
        price: webhookData.market_price,
        stop_loss: webhookData.stop_loss,
        take_profit: webhookData.take_profit,
        status: 'Active'
    };
    
    // Add to trades table
    const trades = [trade];
    updateTradesTable(trades);
    
    // Update active trades count
    const countElement = document.getElementById('activeTradesCount');
    if (countElement) {
        const currentCount = parseInt(countElement.textContent) || 0;
        updateActiveTradesCount(currentCount + 1);
    }
    
    // Update last trade time
    updateLastTradeTime(trade.timestamp);
    
    // Flash the new row to highlight it
    setTimeout(() => {
        const firstRow = document.querySelector('#tradingHistoryTable tbody tr:first-child');
        if (firstRow) {
            firstRow.classList.add('highlight-row');
            setTimeout(() => {
                firstRow.classList.remove('highlight-row');
            }, 3000);
        }
    }, 100);
}

/**
 * Refresh all dashboard data
 */
function refreshAllDashboardData() {
    updateSystemStatus();
    fetchRecentTrades();
    
    const chartPeriod = document.querySelector('.chart-period-btn.active');
    if (chartPeriod) {
        updateChartPeriod(chartPeriod.dataset.period);
    } else {
        updateChartPeriod(30);
    }
    
    // Flash success message
    const refreshBtn = document.getElementById('refreshData');
    if (refreshBtn) {
        const originalText = refreshBtn.innerHTML;
        refreshBtn.innerHTML = '<i class="fa fa-check"></i> Updated';
        
        setTimeout(() => {
            refreshBtn.innerHTML = originalText;
        }, 2000);
    }
}

// Credential Management

document.getElementById('add-credential-form').addEventListener('submit', async (event) => {
  event.preventDefault();

  const serviceName = document.getElementById('service_name').value;
  const apiKey = document.getElementById('api_key').value;
  const encryptedSecret = document.getElementById('encrypted_secret').value;

  try {
    const response = await fetch('/dashboard/api/credentials', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ service_name: serviceName, api_key: apiKey, encrypted_secret: encryptedSecret }),
    });

    if (response.ok) {
      alert('Credential added successfully');
      loadCredentials();
    } else {
      const error = await response.json();
      alert(`Error: ${error.error}`);
    }
  } catch (error) {
    console.error('Error adding credential:', error);
    alert('Failed to add credential');
  }
});

async function loadCredentials() {
  try {
    const response = await fetch('/dashboard/api/credentials');
    if (response.ok) {
      const credentials = await response.json();
      const tableBody = document.getElementById('credentials-table');
      tableBody.innerHTML = '';

      credentials.forEach((credential) => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${credential[1]}</td>
          <td>${credential[2]}</td>
          <td>${credential[3]}</td>
          <td>
            <button class="btn btn-danger btn-sm" onclick="deleteCredential(${credential[0]})">Delete</button>
          </td>
        `;
        tableBody.appendChild(row);
      });
    } else {
      console.error('Failed to load credentials');
    }
  } catch (error) {
    console.error('Error loading credentials:', error);
  }
}

async function deleteCredential(credentialId) {
  if (!confirm('Are you sure you want to delete this credential?')) return;

  try {
    const response = await fetch(`/dashboard/api/credentials/${credentialId}`, {
      method: 'DELETE',
    });

    if (response.ok) {
      alert('Credential deleted successfully');
      loadCredentials();
    } else {
      const error = await response.json();
      alert(`Error: ${error.error}`);
    }
  } catch (error) {
    console.error('Error deleting credential:', error);
    alert('Failed to delete credential');
  }
}

// Load credentials on page load
if (document.getElementById('credentials-table')) {
  loadCredentials();
}