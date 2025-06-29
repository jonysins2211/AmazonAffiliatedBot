/* Modern Cyber Dashboard JavaScript - RafalW3bCraft - Fixed Canvas Version */

// Global variables
let categoryChart = null;
let performanceChart = null;

// Cyber theme colors
const cyberColors = {
    primary: '#00ff41',
    secondary: '#0066ff',
    accent: '#ff0066',
    success: '#00ff66',
    warning: '#ffaa00',
    dark: '#0a0a0a',
    darkAlt: '#1a1a1a'
};

// Initialize dashboard
async function loadDashboardData() {
    try {
        await Promise.all([
            loadStatistics(),
            loadDeals(),
            updateCharts()
        ]);
    } catch (error) {
        console.error('Dashboard load error:', error);
        showNotification('System connection error', 'error');
    }
}

// Load statistics data
async function loadStatistics() {
    try {
        const response = await fetch('/api/stats');
        if (!response.ok) throw new Error('Stats API error');
        
        const stats = await response.json();
        
        // Update statistics with animation
        updateStatWithAnimation('total-deals', stats.total_deals);
        updateStatWithAnimation('active-users', stats.active_users);
        updateStatWithAnimation('total-clicks', stats.total_clicks);
        updateStatWithAnimation('total-earnings', `$${stats.total_earnings.toFixed(2)}`);
        updateStatWithAnimation('conversion-rate', `${stats.conversion_rate.toFixed(1)}%`);
        updateStatWithAnimation('avg-earnings', `$${stats.avg_earnings_per_deal.toFixed(2)}`);
        
        // Store for charts
        window.dashboardStats = stats;
        
    } catch (error) {
        console.error('Statistics load error:', error);
        showNotification('Failed to load statistics', 'error');
    }
}

// Load deals data
async function loadDeals() {
    try {
        const response = await fetch('/api/deals?hours=24&limit=10');
        if (!response.ok) throw new Error('Deals API error');
        
        const deals = await response.json();
        updateDealsTable(deals);
        
    } catch (error) {
        console.error('Deals load error:', error);
        showNotification('Failed to load deals', 'error');
    }
}

// Update charts with proper canvas size validation
async function updateCharts() {
    try {
        if (!window.dashboardStats) return;
        
        const stats = window.dashboardStats;
        
        // Wait for DOM to be ready and check canvas dimensions
        setTimeout(() => {
            const categoryCanvas = document.getElementById('categoryChart');
            const performanceCanvas = document.getElementById('performanceChart');
            
            if (categoryCanvas && isCanvasSafe(categoryCanvas)) {
                updateCategoryChart(stats.category_stats || {});
            }
            
            if (performanceCanvas && isCanvasSafe(performanceCanvas)) {
                updatePerformanceChart(stats);
            }
        }, 100);
        
    } catch (error) {
        console.error('Charts update error:', error);
    }
}

// Validate canvas size to prevent rendering errors
function isCanvasSafe(canvas) {
    const rect = canvas.getBoundingClientRect();
    const maxSize = 2000; // Safe maximum canvas size
    
    return (
        rect.width > 0 && 
        rect.height > 0 && 
        rect.width < maxSize && 
        rect.height < maxSize &&
        canvas.offsetParent !== null // Check if visible
    );
}

// Update category distribution chart with safe rendering
function updateCategoryChart(categoryStats) {
    const ctx = document.getElementById('categoryChart');
    if (!ctx || !isCanvasSafe(ctx)) {
        console.warn('Category chart canvas not ready or unsafe');
        return;
    }
    
    // Destroy existing chart
    if (categoryChart) {
        categoryChart.destroy();
        categoryChart = null;
    }
    
    const labels = Object.keys(categoryStats);
    const data = Object.values(categoryStats);
    
    try {
        // Set explicit canvas size to prevent overflow
        ctx.width = Math.min(ctx.offsetWidth || 300, 500);
        ctx.height = Math.min(ctx.offsetHeight || 300, 500);
        
        categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.length > 0 ? labels : ['No Data'],
                datasets: [{
                    data: data.length > 0 ? data : [1],
                    backgroundColor: [
                        cyberColors.primary,
                        cyberColors.secondary,
                        cyberColors.accent,
                        cyberColors.success,
                        cyberColors.warning
                    ],
                    borderColor: cyberColors.dark,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                devicePixelRatio: Math.min(window.devicePixelRatio || 1, 2),
                animation: {
                    duration: 500
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: cyberColors.primary,
                            font: { 
                                family: 'Orbitron',
                                size: 12
                            },
                            padding: 15
                        }
                    }
                }
            }
        });
        
        console.log('Category chart created successfully');
        
    } catch (error) {
        console.error('Category chart creation failed:', error);
    }
}

// Update performance metrics chart with safe rendering
function updatePerformanceChart(stats) {
    const ctx = document.getElementById('performanceChart');
    if (!ctx || !isCanvasSafe(ctx)) {
        console.warn('Performance chart canvas not ready or unsafe');
        return;
    }
    
    // Destroy existing chart
    if (performanceChart) {
        performanceChart.destroy();
        performanceChart = null;
    }
    
    try {
        // Set explicit canvas size to prevent overflow
        ctx.width = Math.min(ctx.offsetWidth || 400, 600);
        ctx.height = Math.min(ctx.offsetHeight || 300, 400);
        
        performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Deals', 'Clicks', 'Conversions', 'Earnings ($)'],
                datasets: [{
                    label: 'Performance Metrics',
                    data: [
                        stats.total_deals || 0,
                        stats.total_clicks || 0,
                        stats.total_conversions || 0,
                        Math.round(stats.total_earnings || 0)
                    ],
                    borderColor: cyberColors.primary,
                    backgroundColor: cyberColors.primary + '20',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: cyberColors.primary,
                    pointBorderColor: cyberColors.dark,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                devicePixelRatio: Math.min(window.devicePixelRatio || 1, 2),
                animation: {
                    duration: 800
                },
                plugins: {
                    legend: {
                        labels: {
                            color: cyberColors.primary,
                            font: { 
                                family: 'Orbitron',
                                size: 12
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { 
                            color: cyberColors.primary + '30',
                            lineWidth: 1
                        },
                        ticks: { 
                            color: cyberColors.primary,
                            font: { size: 10 }
                        }
                    },
                    x: {
                        grid: { 
                            color: cyberColors.primary + '30',
                            lineWidth: 1
                        },
                        ticks: { 
                            color: cyberColors.primary,
                            font: { size: 10 }
                        }
                    }
                }
            }
        });
        
        console.log('Performance chart created successfully');
        
    } catch (error) {
        console.error('Performance chart creation failed:', error);
    }
}

// Update statistics with animation
function updateStatWithAnimation(elementId, value) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.style.opacity = '0.5';
    element.style.transform = 'scale(0.95)';
    
    setTimeout(() => {
        element.textContent = value;
        element.style.opacity = '1';
        element.style.transform = 'scale(1)';
    }, 150);
}

// Update deals table
function updateDealsTable(deals) {
    const tableBody = document.querySelector('#deals-table tbody');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    if (!deals || deals.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted">
                    <i class="fas fa-info-circle"></i> No deals available
                </td>
            </tr>
        `;
        return;
    }
    
    deals.slice(0, 10).forEach(deal => {
        const row = document.createElement('tr');
        row.className = 'deal-row';
        
        row.innerHTML = `
            <td>
                <div class="deal-title">${deal.title || 'N/A'}</div>
                <small class="text-muted">ASIN: ${deal.asin || 'N/A'}</small>
            </td>
            <td class="text-success font-weight-bold">${deal.price || 'N/A'}</td>
            <td class="text-warning">${deal.discount || 'N/A'}</td>
            <td>
                <span class="badge badge-success">${deal.category || 'general'}</span>
            </td>
            <td class="text-center">${deal.clicks || 0}</td>
            <td class="text-center">${deal.conversions || 0}</td>
            <td class="text-success">$${deal.earnings ? deal.earnings.toFixed(2) : '0.00'}</td>
            <td>
                <span class="badge ${deal.is_active ? 'badge-success' : 'badge-secondary'}">
                    ${deal.is_active ? 'ACTIVE' : 'INACTIVE'}
                </span>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    
    // Initial load
    loadDashboardData();
    
    // Refresh data every 30 seconds
    setInterval(loadDashboardData, 30000);
    
    // Handle window resize for chart responsiveness
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            if (categoryChart) {
                categoryChart.resize();
            }
            if (performanceChart) {
                performanceChart.resize();
            }
        }, 250);
    });
    
    console.log('Dashboard initialized successfully');
});

// CSS styles for notifications
const style = document.createElement('style');
style.textContent = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
        border-radius: 5px;
        border: 1px solid #00ff41;
        background: rgba(0, 255, 65, 0.1);
        color: #00ff41;
    }
    
    .notification.show {
        opacity: 1;
        transform: translateX(0);
    }
    
    .deal-row:hover {
        background-color: rgba(0, 255, 65, 0.05);
        transform: translateX(5px);
        transition: all 0.2s ease;
    }
    
    .rating {
        color: #ffaa00;
    }
    
    .metrics small {
        display: block;
        color: #00ff41;
    }
`;
document.head.appendChild(style);