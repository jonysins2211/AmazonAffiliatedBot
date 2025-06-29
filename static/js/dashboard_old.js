/* Modern Cyber Dashboard JavaScript - RafalW3bCraft */

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
        showOfflineStats();
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
        showOfflineDeals();
    }
}

// Update statistic with cyber animation
function updateStatWithAnimation(elementId, value) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Add glow effect
    element.style.textShadow = '0 0 20px #00ff41, 0 0 30px #00ff41';
    element.style.transform = 'scale(1.1)';
    
    // Update value
    setTimeout(() => {
        element.textContent = value;
        element.style.transform = 'scale(1)';
    }, 200);
}

// Update deals table
function updateDealsTable(deals) {
    const tableBody = document.getElementById('deals-table');
    const dealCount = document.getElementById('deal-count');
    
    if (!tableBody) return;
    
    if (!deals || deals.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center cyber-loading">
                    <i class="fas fa-exclamation-triangle me-2"></i>NO ACTIVE DEALS
                </td>
            </tr>
        `;
        if (dealCount) dealCount.textContent = '0 ACTIVE';
        return;
    }
    
    // Update deal count
    if (dealCount) dealCount.textContent = `${deals.length} ACTIVE`;
    
    // Generate table rows
    const rows = deals.map(deal => {
        const postedTime = deal.posted_at ? formatTimeAgo(new Date(deal.posted_at)) : 'Unknown';
        const earningsColor = deal.earnings > 10 ? 'text-warning' : 'text-info';
        
        return `
            <tr class="fade-in">
                <td>
                    <div class="fw-bold">${truncateText(deal.title, 40)}</div>
                    <small class="text-muted">${postedTime}</small>
                </td>
                <td class="fw-bold cyber-highlight">${deal.price}</td>
                <td>
                    <span class="badge bg-success">${deal.discount}</span>
                </td>
                <td>
                    <span class="badge bg-secondary">${deal.category}</span>
                </td>
                <td class="text-center">
                    <span class="fw-bold">${deal.clicks}</span>
                </td>
                <td class="text-center">
                    <span class="fw-bold text-success">${deal.conversions}</span>
                </td>
                <td class="text-center">
                    <span class="fw-bold ${earningsColor}">$${deal.earnings.toFixed(2)}</span>
                </td>
                <td>
                    <span class="status-indicator me-1"></span>
                    <small class="text-success">ACTIVE</small>
                </td>
            </tr>
        `;
    }).join('');
    
    tableBody.innerHTML = rows;
}

// Update charts
async function updateCharts() {
    if (!window.dashboardStats) return;
    
    updateCategoryChart();
    updatePerformanceChart();
}

// Category distribution chart
function updateCategoryChart() {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;
    
    const stats = window.dashboardStats;
    if (!stats || !stats.category_stats) return;
    
    const labels = Object.keys(stats.category_stats);
    const data = Object.values(stats.category_stats);
    
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    cyberColors.primary,
                    cyberColors.secondary,
                    cyberColors.accent,
                    cyberColors.success,
                    cyberColors.warning
                ],
                borderColor: cyberColors.dark,
                borderWidth: 2,
                hoverBorderWidth: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: cyberColors.primary,
                        font: {
                            family: 'Rajdhani',
                            size: 12,
                            weight: '600'
                        },
                        padding: 15
                    }
                }
            },
            elements: {
                arc: {
                    borderWidth: 2
                }
            }
        }
    });
}

// Performance metrics chart
function updatePerformanceChart() {
    const ctx = document.getElementById('performanceChart');
    if (!ctx) return;
    
    const stats = window.dashboardStats;
    if (!stats) return;
    
    if (performanceChart) {
        performanceChart.destroy();
    }
    
    // Generate sample performance data
    const labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4'];
    const clicksData = [120, 135, 156, stats.total_clicks];
    const conversionsData = [8, 10, 11, stats.total_conversions];
    
    performanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Clicks',
                    data: clicksData,
                    borderColor: cyberColors.secondary,
                    backgroundColor: cyberColors.secondary + '20',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'Conversions',
                    data: conversionsData,
                    borderColor: cyberColors.success,
                    backgroundColor: cyberColors.success + '20',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: cyberColors.primary,
                        font: {
                            family: 'Rajdhani',
                            size: 12,
                            weight: '600'
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: cyberColors.primary,
                        font: {
                            family: 'Rajdhani'
                        }
                    },
                    grid: {
                        color: cyberColors.primary + '30'
                    }
                },
                y: {
                    ticks: {
                        color: cyberColors.primary,
                        font: {
                            family: 'Rajdhani'
                        }
                    },
                    grid: {
                        color: cyberColors.primary + '30'
                    }
                }
            }
        }
    });
}

// Utility functions
function formatTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffHours > 24) {
        return `${Math.floor(diffHours / 24)}d ago`;
    } else if (diffHours > 0) {
        return `${diffHours}h ago`;
    } else if (diffMins > 0) {
        return `${diffMins}m ago`;
    } else {
        return 'Just now';
    }
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function showNotification(message, type = 'info') {
    const colors = {
        success: cyberColors.success,
        error: cyberColors.accent,
        warning: cyberColors.warning,
        info: cyberColors.secondary
    };
    
    const notification = document.createElement('div');
    notification.className = 'position-fixed top-0 end-0 m-3';
    notification.style.zIndex = '9999';
    notification.innerHTML = `
        <div class="alert alert-dismissible fade show" style="
            background: ${cyberColors.darkAlt};
            border: 1px solid ${colors[type]};
            color: ${colors[type]};
            box-shadow: 0 0 10px ${colors[type]};
        ">
            <i class="fas fa-info-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function showOfflineStats() {
    // Show cached or default stats when offline
    const elements = [
        'total-deals', 'active-users', 'total-clicks', 
        'total-earnings', 'conversion-rate', 'avg-earnings'
    ];
    
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element && element.textContent === '--') {
            element.textContent = 'OFFLINE';
            element.style.color = cyberColors.accent;
        }
    });
}

function showOfflineDeals() {
    const tableBody = document.getElementById('deals-table');
    if (tableBody) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center cyber-loading">
                    <i class="fas fa-wifi me-2" style="color: ${cyberColors.accent};"></i>
                    SYSTEM OFFLINE - DATA UNAVAILABLE
                </td>
            </tr>
        `;
    }
}

// Matrix effect for background
function initMatrixEffect() {
    const canvas = document.createElement('canvas');
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '-1';
    canvas.style.opacity = '0.1';
    document.body.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';
    const charArray = chars.split('');
    const fontSize = 14;
    const columns = canvas.width / fontSize;
    const drops = Array(Math.floor(columns)).fill(1);
    
    function drawMatrix() {
        ctx.fillStyle = 'rgba(10, 10, 10, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = cyberColors.primary;
        ctx.font = `${fontSize}px monospace`;
        
        for (let i = 0; i < drops.length; i++) {
            const text = charArray[Math.floor(Math.random() * charArray.length)];
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);
            
            if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                drops[i] = 0;
            }
            drops[i]++;
        }
    }
    
    setInterval(drawMatrix, 100);
    
    // Resize handler
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize matrix effect
    initMatrixEffect();
    
    // Load dashboard data
    loadDashboardData();
    
    // Set up auto-refresh
    setInterval(loadDashboardData, 30000);
    
    // Add cyber glow effects to interactive elements
    document.querySelectorAll('.cyber-stat-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.boxShadow = '0 0 20px #00ff41, 0 0 30px #00ff41';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.boxShadow = '0 0 10px #00ff41';
        });
    });
});

// Global refresh function
function refreshDashboard() {
    const btn = document.querySelector('[onclick="refreshDashboard()"]');
    if (btn) {
        const icon = btn.querySelector('i');
        if (icon) {
            icon.classList.add('fa-spin');
            loadDashboardData().finally(() => {
                icon.classList.remove('fa-spin');
            });
        }
    }
    
    showNotification('Dashboard refreshed', 'success');
}