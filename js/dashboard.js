let dashboardCharts = {
    byType: null,
    byStatus: null,
    trend: null
};

// Guard against concurrent loadDashboard() calls (fast re-navigation)
let _dashboardLoading = false;

function loadDashboard(forceRefresh = false) {
    if (_dashboardLoading) return Promise.resolve();
    if (forceRefresh || !Array.isArray(records) || records.length === 0) {
        _dashboardLoading = true;
        return loadRecords()
            .then(fetchedRecords => {
                refreshDashboardData(fetchedRecords || []);
            })
            .finally(() => {
                _dashboardLoading = false;
            });
    }

    refreshDashboardData(records);
    return Promise.resolve(records);
}

function refreshDashboardData(sourceRecords) {
    const safeRecords = Array.isArray(sourceRecords) ? sourceRecords : [];

    updateDashboardSummary(safeRecords);
    updateDashboardActivity(safeRecords);
    renderDashboardCharts(safeRecords);
}

function updateDashboardSummary(sourceRecords) {
    const totals = sourceRecords.reduce((acc, record) => {
        const status = (record.status || '').toLowerCase();
        acc.total += 1;
        if (status === 'pending') acc.pending += 1;
        if (status === 'approved') acc.approved += 1;
        if (status === 'rejected') acc.rejected += 1;
        return acc;
    }, { total: 0, pending: 0, approved: 0, rejected: 0 });

    setDashboardValue('dashboardTotalRecords', totals.total);
    setDashboardValue('dashboardPendingRecords', totals.pending);
    setDashboardValue('dashboardApprovedRecords', totals.approved);
    setDashboardValue('dashboardRejectedRecords', totals.rejected);
}

function setDashboardValue(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function updateDashboardActivity(sourceRecords) {
    const tbody = document.getElementById('dashboardRecentActivity');
    if (!tbody) return;

    const recent = [...sourceRecords]
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 6);

    if (recent.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="dashboard-empty-state">No records available yet.</td></tr>';
        return;
    }

    tbody.innerHTML = recent.map(record => `
        <tr>
            <td>${record.id}</td>
            <td>${record.name}</td>
            <td>${formatType(record.type)}</td>
            <td><span class="dashboard-status-pill ${formatStatusClass(record.status)}">${record.status}</span></td>
            <td>${formatDashboardDate(record.date)}</td>
        </tr>
    `).join('');
}

function renderDashboardCharts(sourceRecords) {
    if (typeof Chart === 'undefined') {
        showNotification('Chart.js failed to load for the dashboard.', 'error');
        return;
    }

    const typeCounts = countBy(sourceRecords, record => formatType(record.type));
    const statusCounts = countBy(sourceRecords, record => record.status || 'Unknown');
    const monthlyCounts = countByMonth(sourceRecords);

    dashboardCharts.byType = renderChart(
        'recordsByTypeChart',
        dashboardCharts.byType,
        'doughnut',
        {
            labels: Object.keys(typeCounts),
            datasets: [{
                data: Object.values(typeCounts),
                backgroundColor: ['#3498db', '#9b59b6', '#27ae60', '#f39c12', '#2c3e50'],
                borderWidth: 0
            }]
        },
        {
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            maintainAspectRatio: false
        }
    );

    dashboardCharts.byStatus = renderChart(
        'recordsByStatusChart',
        dashboardCharts.byStatus,
        'bar',
        {
            labels: Object.keys(statusCounts),
            datasets: [{
                label: 'Records',
                data: Object.values(statusCounts),
                backgroundColor: ['#f39c12', '#27ae60', '#e74c3c', '#3498db'],
                borderRadius: 10,
                maxBarThickness: 56
            }]
        },
        {
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            maintainAspectRatio: false
        }
    );

    dashboardCharts.trend = renderChart(
        'recordsTrendChart',
        dashboardCharts.trend,
        'line',
        {
            labels: Object.keys(monthlyCounts),
            datasets: [{
                label: 'Records',
                data: Object.values(monthlyCounts),
                borderColor: '#1ec77c',
                backgroundColor: 'rgba(30, 199, 124, 0.16)',
                fill: true,
                tension: 0.35,
                pointRadius: 4,
                pointBackgroundColor: '#1ec77c'
            }]
        },
        {
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            maintainAspectRatio: false
        }
    );
}

function renderChart(canvasId, currentChart, type, data, options) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return currentChart;

    if (currentChart) {
        currentChart.destroy();
    }

    return new Chart(canvas, {
        type,
        data: ensureChartData(data),
        options: Object.assign({
            responsive: true
        }, options || {})
    });
}

function ensureChartData(data) {
    if (data.labels.length > 0) return data;

    return {
        labels: ['No Data'],
        datasets: [{
            data: [1],
            backgroundColor: ['#dfe7ec'],
            borderWidth: 0
        }]
    };
}

function countBy(sourceRecords, keyGetter) {
    return sourceRecords.reduce((acc, record) => {
        const key = keyGetter(record) || 'Unknown';
        acc[key] = (acc[key] || 0) + 1;
        return acc;
    }, {});
}

function countByMonth(sourceRecords) {
    const now = new Date();
    const labels = [];
    const counts = {};

    for (let i = 5; i >= 0; i--) {
        const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
        const key = date.toLocaleString('en-US', { month: 'short', year: 'numeric' });
        labels.push(key);
        counts[key] = 0;
    }

    sourceRecords.forEach(record => {
        const parsedDate = new Date(record.date);
        if (Number.isNaN(parsedDate.getTime())) return;
        const key = parsedDate.toLocaleString('en-US', { month: 'short', year: 'numeric' });
        if (Object.prototype.hasOwnProperty.call(counts, key)) {
            counts[key] += 1;
        }
    });

    return labels.reduce((acc, label) => {
        acc[label] = counts[label];
        return acc;
    }, {});
}

function formatStatusClass(status) {
    return (status || 'unknown').toString().trim().toLowerCase().replace(/\s+/g, '-');
}

function formatDashboardDate(value) {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value || '-';
    return parsed.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}