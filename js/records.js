// =============================================================
//  js/records.js — loadRecords (DB fetch), displayRecords,
//                  search, filter, clearFilters, formatType
//  Requires: globals.js, navigation.js
// =============================================================

function displayRecords(recordsToDisplay) {
    const tbody = document.getElementById('recordsTableBody');
    tbody.innerHTML = '';
    if (recordsToDisplay.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="no-records">No records found</td></tr>';
        return;
    }
    recordsToDisplay.forEach(record => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${record.id}</td>
            <td>${formatType(record.type)}</td>
            <td>${record.name}</td>
            <td>${record.date}</td>
            <td>${record.status}</td>
            <td><button class="btn-edit-record" onclick="viewRecord(records.find(r => r.id === '${record.id}'))">&#9998; Edit</button></td>
        `;
        tbody.appendChild(row);
    });
}

// Fetch Records from PHP Backend
function loadRecords() {
    const tbody = document.getElementById('recordsTableBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;color:#888;">Loading records...</td></tr>';

    fetch('php/get_records.php')
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            showNotification('Database error: ' + data.error, 'error');
            if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="no-records">Failed to load records.</td></tr>';
            return;
        }
        records = data.map(row => ({
            id:       row.id,
            doc_id:   row.doc_id,
            type:     row.type,
            name:     row.name,
            date:     row.date,
            status:   row.status,
            formData: row.formData || {}
        }));
        displayRecords(records);
    })
    .catch(() => {
        showNotification('Cannot reach server. Check that XAMPP is running.', 'error');
        if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="no-records">Server not reachable.</td></tr>';
    });
}

function formatType(type) {
    const types = {
        'birth': 'Birth Certificate',
        'death': 'Death Certificate',
        'marriage-cert': 'Marriage Certificate',
        'marriage-license': 'Marriage License'
    };
    return types[type] || type;
}

function handleSearchKeypress(event) {
    if (event.key === 'Enter') {
        searchRecords();
    }
}

function searchRecords() {
    filterRecords();
}

function filterRecords() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const typeFilter = document.getElementById('typeSelect').value;
    const statusFilter = document.getElementById('statusSelect').value;
    const dateFilter = document.getElementById('dateFilter').value;

    let filtered = records.filter(record => {
        // Search filter
        const matchesSearch = searchTerm === '' || 
            record.name.toLowerCase().includes(searchTerm) ||
            record.id.toLowerCase().includes(searchTerm);
        
        // Type filter
        const matchesType = !typeFilter || record.type === typeFilter;
        
        // Status filter
        const matchesStatus = !statusFilter || record.status === statusFilter;
        
        // Date filter
        let matchesDate = true;
        if (dateFilter) {
            const recordDate = new Date(record.date);
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            switch(dateFilter) {
                case 'today':
                    const todayStart = new Date(today);
                    matchesDate = recordDate >= todayStart;
                    break;
                case 'week':
                    const weekStart = new Date(today);
                    weekStart.setDate(today.getDate() - 7);
                    matchesDate = recordDate >= weekStart;
                    break;
                case 'month':
                    const monthStart = new Date(today);
                    monthStart.setDate(today.getDate() - 30);
                    matchesDate = recordDate >= monthStart;
                    break;
                case 'year':
                    const yearStart = new Date(today);
                    yearStart.setFullYear(today.getFullYear() - 1);
                    matchesDate = recordDate >= yearStart;
                    break;
            }
        }
        
        return matchesSearch && matchesType && matchesStatus && matchesDate;
    });

    displayRecords(filtered);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('typeSelect').value = '';
    document.getElementById('statusSelect').value = '';
    document.getElementById('dateFilter').value = '';
    displayRecords(records);
}
