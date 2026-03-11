// ============================================================
//  RECORDS — Load, display, search, filter
//  Depends on: globals.js, navigation.js
// ============================================================

// ── Load records from DB → php/get_records.php ───────────────
function loadRecords() {
    const tbody = document.getElementById('recordsTableBody');
    tbody.innerHTML = '<tr><td colspan="6" class="no-records">Loading records...</td></tr>';

    fetch('php/get_records.php')
        .then(res => {
            if (!res.ok) throw new Error('Server returned ' + res.status);
            return res.json();
        })
        .then(data => {
            if (data.error) {
                showNotification('DB error: ' + data.error, 'error');
                tbody.innerHTML = '<tr><td colspan="6" class="no-records">Failed to load records.</td></tr>';
                return;
            }
            records = data;
            displayRecords(records);
        })
        .catch(err => {
            showNotification('Could not load records. Is XAMPP running?', 'error');
            tbody.innerHTML = '<tr><td colspan="6" class="no-records">Could not connect to database.</td></tr>';
            console.error('loadRecords error:', err);
        });
}

// ── Display ───────────────────────────────────────────────────
function displayRecords(recordsToDisplay) {
    const tbody = document.getElementById('recordsTableBody');
    tbody.innerHTML = '';

    if (!recordsToDisplay || recordsToDisplay.length === 0) {
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

// ── Helpers ───────────────────────────────────────────────────
function formatType(type) {
    const map = {
        'birth':            'Birth Certificate',
        'death':            'Death Certificate',
        'marriage-cert':    'Marriage Certificate',
        'marriage-license': 'Marriage License'
    };
    return map[type] || type;
}

function handleSearchKeypress(event) {
    if (event.key === 'Enter') filterRecords();
}

function searchRecords() {
    filterRecords();
}

// ── Filter (client-side against the loaded records array) ─────
function filterRecords() {
    const search     = document.getElementById('searchInput').value.toLowerCase();
    const typeFilter = document.getElementById('typeSelect').value;
    const statusFilt = document.getElementById('statusSelect').value;
    const dateFilt   = document.getElementById('dateFilter').value;

    const filtered = records.filter(record => {
        const matchesSearch = !search ||
            record.name.toLowerCase().includes(search) ||
            record.id.toLowerCase().includes(search);

        const matchesType   = !typeFilter || record.type   === typeFilter;
        const matchesStatus = !statusFilt || record.status === statusFilt;

        let matchesDate = true;
        if (dateFilt) {
            const recordDate = new Date(record.date);
            const today      = new Date();
            today.setHours(0, 0, 0, 0);
            switch (dateFilt) {
                case 'today': { matchesDate = recordDate >= today; break; }
                case 'week':  { const w = new Date(today); w.setDate(today.getDate() - 7);  matchesDate = recordDate >= w; break; }
                case 'month': { const m = new Date(today); m.setDate(today.getDate() - 30); matchesDate = recordDate >= m; break; }
                case 'year':  { const y = new Date(today); y.setFullYear(today.getFullYear() - 1); matchesDate = recordDate >= y; break; }
            }
        }

        return matchesSearch && matchesType && matchesStatus && matchesDate;
    });

    displayRecords(filtered);
}

function clearFilters() {
    document.getElementById('searchInput').value  = '';
    document.getElementById('typeSelect').value   = '';
    document.getElementById('statusSelect').value = '';
    document.getElementById('dateFilter').value   = '';
    displayRecords(records);
}
