// Jamso AI Dashboard Scripts
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

function updateDateTime() {
    const dateTimeEl = document.getElementById('dashboardDateTime');
    if (dateTimeEl) {
        const now = new Date();
        dateTimeEl.textContent = now.toLocaleString();
    }
}

function startDateTimeUpdater() {
    updateDateTime();
    setInterval(updateDateTime, 1000);
}
