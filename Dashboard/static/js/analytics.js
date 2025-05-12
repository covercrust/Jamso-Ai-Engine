/**
 * Jamso AI Trading Bot - Analytics Dashboard JavaScript
 * Enhancements:
 * - Added detailed comments for better understanding.
 * - Optimized code for performance and maintainability.
 */

// Initialize analytics when DOM content is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize date picker defaults
    initDatePicker();

    // Load initial performance data (30 days by default)
    loadPerformanceData(30);

    // Set up event listeners
    setupEventListeners();
});

/**
 * Initialize the date picker with default values.
 *
 * Purpose:
 * - Sets up the date picker for selecting date ranges.
 * - Ensures default values are applied on page load.
 */
function initDatePicker() {
    console.log("Initializing date picker.");
    // Set default dates for custom range (last 30 days)
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 30);

    document.getElementById('startDate').valueAsDate = thirtyDaysAgo;
    document.getElementById('endDate').valueAsDate = today;
}

/**
 * Set up all analytics dashboard event listeners.
 *
 * Purpose:
 * - Handles user interactions with the dashboard.
 * - Updates the UI based on user input.
 */
function setupEventListeners() {
    // Date range selector
    document.getElementById('dateRangeSelect').addEventListener('change', function() {
        const customRange = document.getElementById('customDateRange');
        if (this.value === 'custom') {
            customRange.style.display = 'flex';
        } else {
            customRange.style.display = 'none';
        }
    });

    // Update button
    document.getElementById('updateAnalytics').addEventListener('click', function() {
        const dateRangeSelect = document.getElementById('dateRangeSelect');
        const selectedValue = dateRangeSelect.value;

        if (selectedValue === 'custom') {
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;

            if (startDate && endDate) {
                // Calculate days between the two dates
                const start = new Date(startDate);
                const end = new Date(endDate);
                const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24));

                loadPerformanceData(days, start.toISOString().split('T')[0]);
            } else {
                alert('Please select both start and end dates');
            }
        } else {
            // Use the selected preset days
            loadPerformanceData(parseInt(selectedValue));
        }
    });
}

/**
 * Load performance data from the server.
 *
 * Purpose:
 * - Fetches analytics data based on the selected date range.
 * - Updates the dashboard with the fetched data.
 *
 * @param {number} days - Number of days to fetch data for.
 * @param {string} startDate - Optional start date (YYYY-MM-DD format).
 */
function loadPerformanceData(days, startDate = null) {
    console.log(`Loading performance data for ${days} days starting from ${startDate || 'default range'}.`);
    // Show loading state
    showLoadingState();

    // Construct the API URL
    let apiUrl = `/dashboard/api/performance/${days}`;
    if (startDate) {
        apiUrl += `?start_date=${startDate}`;
    }

    // Fetch data from the server
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Update the charts with the new data
            updateCharts(data);

            // Update summary metrics
            updateSummaryMetrics(data);

            // Hide loading state
            hideLoadingState();
        })
        .catch(error => {
            console.error('Error fetching performance data:', error);
            // Hide loading state
            hideLoadingState();

            // Show error message
            alert('Failed to load performance data. Please try again later.');
        });
}

/**
 * Show loading state while data is being fetched.
 *
 * Purpose:
 * - Provides visual feedback to the user during data fetching.
 */
function showLoadingState() {
    const chartContainers = document.querySelectorAll('.chart-container');
    chartContainers.forEach(container => {
        container.classList.add('loading');
        container.style.opacity = '0.5';
    });
}

/**
 * Hide loading state after data is fetched.
 *
 * Purpose:
 * - Restores the UI to its normal state after data fetching.
 */
function hideLoadingState() {
    const chartContainers = document.querySelectorAll('.chart-container');
    chartContainers.forEach(container => {
        container.classList.remove('loading');
        container.style.opacity = '1';
    });
}

/**
 * Update all charts with new data.
 *
 * Purpose:
 * - Refreshes the analytics charts with the latest data.
 *
 * @param {Object} data - Performance data from the server.
 */
function updateCharts(data) {
    // Destroy existing charts to prevent memory leaks
    destroyExistingCharts();

    // Create new charts with the data
    createProfitLossChart(data.daily_performance);
    createWinLossPieChart(data.win_loss);
    createInstrumentChart(data.instrument_breakdown);
    createDailyPerformanceChart(data.weekday_performance);
}

/**
 * Destroy existing chart instances to prevent memory leaks.
 *
 * Purpose:
 * - Ensures old chart instances are removed before creating new ones.
 */
function destroyExistingCharts() {
    const chartIds = ['profitLossChart', 'winLossPieChart', 'instrumentChart', 'dailyPerformanceChart'];

    chartIds.forEach(id => {
        const chartElement = document.getElementById(id);
        const chartInstance = Chart.getChart(chartElement);

        if (chartInstance) {
            chartInstance.destroy();
        }
    });
}

/**
 * Create the profit/loss over time chart.
 *
 * Purpose:
 * - Visualizes account balance changes over time.
 *
 * @param {Array} dailyData - Daily performance data.
 */
function createProfitLossChart(dailyData) {
    const dates = dailyData.map(item => item.date);
    const balances = dailyData.map(item => item.balance);

    const profitLossCtx = document.getElementById('profitLossChart');
    new Chart(profitLossCtx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Account Balance',
                data: balances,
                borderColor: 'rgba(78, 115, 223, 1)',
                backgroundColor: 'rgba(78, 115, 223, 0.05)',
                pointRadius: 3,
                pointBackgroundColor: 'rgba(78, 115, 223, 1)',
                pointBorderColor: 'rgba(78, 115, 223, 1)',
                pointHoverRadius: 3,
                pointHoverBackgroundColor: 'rgba(78, 115, 223, 1)',
                pointHoverBorderColor: 'rgba(78, 115, 223, 1)',
                pointHitRadius: 10,
                pointBorderWidth: 2,
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    ticks: {
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create the win/loss distribution pie chart.
 *
 * Purpose:
 * - Displays the proportion of winning and losing trades.
 *
 * @param {Object} winLossData - Win/loss data.
 */
function createWinLossPieChart(winLossData) {
    const winLossCtx = document.getElementById('winLossPieChart');
    new Chart(winLossCtx, {
        type: 'pie',
        data: {
            labels: ['Winning Trades', 'Losing Trades'],
            datasets: [{
                data: [winLossData.winning_trades, winLossData.losing_trades],
                backgroundColor: ['#1cc88a', '#e74a3b'],
                hoverBackgroundColor: ['#169a6f', '#be3c30'],
                hoverBorderColor: 'rgba(234, 236, 244, 1)'
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

/**
 * Create the trade volume by instrument chart.
 *
 * Purpose:
 * - Shows the number of trades for each instrument.
 *
 * @param {Array} instrumentData - Instrument data.
 */
function createInstrumentChart(instrumentData) {
    const labels = instrumentData.map(item => item.instrument);
    const counts = instrumentData.map(item => item.count);

    const instrumentCtx = document.getElementById('instrumentChart');
    new Chart(instrumentCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Trades',
                data: counts,
                backgroundColor: [
                    'rgba(78, 115, 223, 0.8)',
                    'rgba(28, 200, 138, 0.8)',
                    'rgba(54, 185, 204, 0.8)',
                    'rgba(246, 194, 62, 0.8)',
                    'rgba(231, 74, 59, 0.8)',
                    'rgba(133, 135, 150, 0.8)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Create the daily performance by weekday chart.
 *
 * Purpose:
 * - Highlights average profit/loss for each weekday.
 *
 * @param {Array} weekdayData - Performance by weekday.
 */
function createDailyPerformanceChart(weekdayData) {
    const labels = weekdayData.map(item => item.weekday);
    const values = weekdayData.map(item => item.average_profit);

    const dailyPerformanceCtx = document.getElementById('dailyPerformanceChart');
    new Chart(dailyPerformanceCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Average Profit/Loss',
                data: values,
                backgroundColor: function(context) {
                    const value = context.dataset.data[context.dataIndex];
                    return value >= 0 ? 'rgba(28, 200, 138, 0.8)' : 'rgba(231, 74, 59, 0.8)';
                }
            }]
        },
        options: {
            maintainAspectRatio: false,
            scales: {
                y: {
                    ticks: {
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Update summary metrics with new data.
 *
 * Purpose:
 * - Refreshes the summary cards with the latest analytics data.
 *
 * @param {Object} data - Performance data.
 */
function updateSummaryMetrics(data) {
    // Update the summary cards with the new data
    document.querySelector('.card:nth-child(1) .h5').textContent = data.summary.total_trades;
    document.querySelector('.card:nth-child(2) .h5').textContent = data.summary.profit_loss;

    // Update win rate and progress bar
    const winRateElement = document.querySelector('.card:nth-child(3) .h5');
    const progressBar = document.querySelector('.progress-bar');

    winRateElement.textContent = data.summary.win_rate + '%';
    progressBar.style.width = data.summary.win_rate + '%';

    // Update average duration
    document.querySelector('.card:nth-child(4) .h5').textContent = data.summary.avg_duration;
}