// Jamso AI Dashboard Scripts
// Enhancements:
// - Added detailed comments for better understanding.
// - Optimized code for maintainability and clarity.

console.log("Script.js is loaded!");

// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded");

    // Initialize dashboard components
    initializeDashboard();

    // Set up event listeners
    setupEventListeners();

    // Start date/time updater if element exists
    if (document.getElementById('dashboardDateTime')) {
        startDateTimeUpdater();
    }
});

/**
 * Update the date and time on the dashboard.
 *
 * Purpose:
 * - Keeps the displayed date and time current.
 */
function updateDateTime() {
    const dateTimeEl = document.getElementById('dashboardDateTime');
    if (dateTimeEl) {
        const now = new Date();
        dateTimeEl.textContent = now.toLocaleString();
    }
}

/**
 * Start the date/time updater.
 *
 * Purpose:
 * - Ensures the date and time are updated every second.
 */
function startDateTimeUpdater() {
    updateDateTime();
    setInterval(updateDateTime, 1000);
}
