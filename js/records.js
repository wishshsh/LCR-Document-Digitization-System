// Records Management
function displayRecords(recordsToDisplay) {
    const tbody = document.getElementById('recordsTableBody');
    tbody.innerHTML = '';

    if (recordsToDisplay.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="no-records">No records found</td></tr>';
        return;
    }

    recordsToDisplay.forEach(record => {
        const row = document.createElement('tr');
        row.style.cursor = 'pointer';
        row.onclick = () => viewRecord(record);
        row.innerHTML = `
            <td>${record.id}</td>
            <td>${formatType(record.type)}</td>
            <td>${record.name}</td>
            <td>${record.date}</td>
            <td>${record.status}</td>
        `;
        tbody.appendChild(row);
    });
}

function viewRecord(record) {
    alert(`Record Details:\n\nID: ${record.id}\nType: ${formatType(record.type)}\nName: ${record.name}\nDate: ${record.date}\nStatus: ${record.status}`);
}

// Fetch Records from PHP Backend
function loadRecords() {
    fetch('php/get_records.php')
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Database error:', data.error);
            return;
        }
        
        records = data.map(dbRow => ({
            id: 'DOC-' + dbRow.doc_id,
            type: dbRow.type_name.toLowerCase().replace(' ', '-'),
            name: dbRow.uploader_name,
            date: dbRow.upload_date.split(' ')[0],
            status: dbRow.status || 'Pending'
        }));

        displayRecords(records);
    })
    .catch(error => console.error('Error loading records:', error));
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
        const matchesSearch = searchTerm === '' || 
            record.name.toLowerCase().includes(searchTerm) ||
            record.id.toLowerCase().includes(searchTerm);
        
        const matchesType = !typeFilter || record.type === typeFilter;
        const matchesStatus = !statusFilter || record.status === statusFilter;
        
        let matchesDate = true;
        if (dateFilter) {
            const recordDate = new Date(record.date);
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            switch(dateFilter) {
                case 'today':
                    matchesDate = recordDate >= new Date(today);
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
