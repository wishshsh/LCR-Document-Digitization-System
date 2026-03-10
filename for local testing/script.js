// Global variables
let uploadedFiles = {
    cert: [],
    marriage: []
};

let records = [
    { id: 'BC-001', type: 'birth', name: 'Maria Santos', date: '2025-01-10', status: 'Approved' },
    { id: 'BC-002', type: 'birth', name: 'Jose Reyes', date: '2025-01-15', status: 'Pending' },
    { id: 'BC-003', type: 'birth', name: 'Ana Dela Cruz', date: '2025-02-03', status: 'Pending' },
    { id: 'DC-001', type: 'death', name: 'Roberto Villanueva', date: '2025-02-14', status: 'Approved' },
    { id: 'DC-002', type: 'death', name: 'Lourdes Magno', date: '2025-03-01', status: 'Rejected' },
    { id: 'MC-001', type: 'marriage-cert', name: 'Carlos & Elena Bautista', date: '2025-01-28', status: 'Approved' },
    { id: 'MC-002', type: 'marriage-cert', name: 'Ramon & Sofia Dizon', date: '2025-02-20', status: 'Pending' },
    { id: 'ML-001', type: 'marriage-license', name: 'Paolo & Kristine Mendoza', date: '2025-03-05', status: 'Pending' },
    { id: 'ML-002', type: 'marriage-license', name: 'Angelo & Camille Torres', date: '2025-03-06', status: 'Approved' },
    { id: 'BC-004', type: 'birth', name: 'Gabrielle Ramos', date: '2025-03-07', status: 'Pending' }
];

// Navigation history
let navigationHistory = ['login'];
let currentHistoryIndex = 0;
let isLoggedIn = false;

// User data
let currentUser = {
    username: '',
    name: 'Admin User',
    email: 'admin@localregistry.gov.ph',
    role: 'Administrator',
    department: 'Civil Registry Office',
    employeeId: 'EMP-2024-001'
};

// Page URLs mapping (for potential future use)
const pageUrls = {
    'login': 'https://localcivilregistry.gov.ph',
    'services': 'https://localcivilregistry.gov.ph/services',
    'certifications': 'https://localcivilregistry.gov.ph/services/certifications',
    'certTemplateView': 'https://localcivilregistry.gov.ph/services/certifications/template',
    'marriageLicense': 'https://localcivilregistry.gov.ph/services/marriage-license',
    'marriageTemplateView': 'https://localcivilregistry.gov.ph/services/marriage-license/template',
    'records': 'https://localcivilregistry.gov.ph/records',
    'profile': 'https://localcivilregistry.gov.ph/profile'
};

// Update back button visibility
function updateBackButton() {
    const backButton = document.getElementById('backButton');
    const currentPage = navigationHistory[currentHistoryIndex];
    
    // Show back button if not on login or services page and logged in
    if (isLoggedIn && currentHistoryIndex > 0 && currentPage !== 'services') {
        backButton.style.display = 'flex';
    } else {
        backButton.style.display = 'none';
    }
}

// Go back in navigation history
function goBack() {
    if (currentHistoryIndex > 0) {
        currentHistoryIndex--;
        const previousPage = navigationHistory[currentHistoryIndex];
        showPage(previousPage, false);
    }
}

// Page Navigation with history
function showPage(pageName, addToHistory = true) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.remove('active'));
    
    const targetPage = document.getElementById(pageName + 'Page');
    if (targetPage) {
        targetPage.classList.add('active');
        
        // Update navigation history
        if (addToHistory) {
            // Remove forward history when navigating to a new page
            navigationHistory = navigationHistory.slice(0, currentHistoryIndex + 1);
            navigationHistory.push(pageName);
            currentHistoryIndex = navigationHistory.length - 1;
        }
        
        // Update back button visibility
        updateBackButton();
        
        // Close user menu when navigating
        closeUserMenu();
    }

    // Show records when navigating to records page
    if (pageName === 'records') {
        loadRecords();
    }
    
    // Update profile page when navigating to it
    if (pageName === 'profile') {
        updateProfilePage();
    }
}

// Toggle user menu
function toggleUserMenu() {
    const userMenu = document.getElementById('userMenu');
    if (userMenu.style.display === 'none' || userMenu.style.display === '') {
        userMenu.style.display = 'block';
        // Update user info in menu
        document.getElementById('userName').textContent = currentUser.name;
        document.getElementById('userEmail').textContent = currentUser.email;
    } else {
        userMenu.style.display = 'none';
    }
}

// Close user menu
function closeUserMenu() {
    const userMenu = document.getElementById('userMenu');
    userMenu.style.display = 'none';
}

// View profile
function viewProfile() {
    showPage('profile');
}

// Update profile page with current user data
function updateProfilePage() {
    document.getElementById('profileName').value = currentUser.name;
    document.getElementById('profileEmail').value = currentUser.email;
    document.getElementById('profileUsername').value = currentUser.username;
    document.getElementById('profileRole').value = currentUser.role;
    document.getElementById('profileDepartment').value = currentUser.department;
    document.getElementById('profileEmployeeId').value = currentUser.employeeId;
}

// Edit Profile Modal Functions
function openEditProfileModal() {
    document.getElementById('editName').value = currentUser.name;
    document.getElementById('editEmail').value = currentUser.email;
    document.getElementById('editDepartment').value = currentUser.department;
    document.getElementById('editProfileModal').style.display = 'flex';
}

function closeEditProfileModal() {
    document.getElementById('editProfileModal').style.display = 'none';
    // Clear form
    document.getElementById('editName').value = '';
    document.getElementById('editEmail').value = '';
    document.getElementById('editDepartment').value = '';
}

function saveProfileChanges(event) {
    event.preventDefault();
    
    // Update user data
    currentUser.name = document.getElementById('editName').value;
    currentUser.email = document.getElementById('editEmail').value;
    currentUser.department = document.getElementById('editDepartment').value;
    
    // Update profile page
    updateProfilePage();
    
    // Update user menu
    document.getElementById('userName').textContent = currentUser.name;
    document.getElementById('userEmail').textContent = currentUser.email;
    
    // Close modal
    closeEditProfileModal();
    
    // Show success message
    showNotification('Profile updated successfully!', 'success');
}

// Change Password Modal Functions
function openChangePasswordModal() {
    document.getElementById('changePasswordModal').style.display = 'flex';
}

function closeChangePasswordModal() {
    document.getElementById('changePasswordModal').style.display = 'none';
    // Clear form
    document.getElementById('currentPassword').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('confirmPassword').value = '';
}

function changePassword(event) {
    event.preventDefault();
    
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    // Validate passwords match
    if (newPassword !== confirmPassword) {
        showNotification('New passwords do not match!', 'error');
        return;
    }
    
    // Validate password length
    if (newPassword.length < 8) {
        showNotification('Password must be at least 8 characters long!', 'error');
        return;
    }
    
    // In a real application, this would verify the current password with the server
    // For this demo, we'll just accept it
    
    // Close modal
    closeChangePasswordModal();
    
    // Show success message
    showNotification('Password changed successfully!', 'success');
}

// Notification function
function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to body
    document.body.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Home navigation
function goHome() {
    if (isLoggedIn) {
        showPage('services');
    }
}

// Logout function
function logout() {
    closeUserMenu();
    if (confirm('Are you sure you want to logout?')) {
        isLoggedIn = false;
        document.getElementById('headerButtons').style.display = 'none';
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
        uploadedFiles = { cert: [], marriage: [] };
        navigationHistory = ['login'];
        currentHistoryIndex = 0;
        currentUser.username = '';
        showPage('login', false);
        updateBackButton();
    }
}

// Login via PHP Backend
function login(event) {
    event.preventDefault();
    const usernameInput = document.getElementById('username').value;
    const passwordInput = document.getElementById('password').value;

    if (!usernameInput || !passwordInput) {
        showNotification('Please enter both username and password', 'error');
        return;
    }

    // --- MOCK LOGIN ---
    const mockUsers = [
        { username: 'admin', password: 'admin123', name: 'Admin User', role: 'Administrator' },
        { username: 'staff', password: 'staff123', name: 'Staff Member', role: 'Staff' }
    ];
    const matched = mockUsers.find(u => u.username === usernameInput && u.password === passwordInput);
    if (matched) {
        isLoggedIn = true;
        currentUser.username = matched.username;
        currentUser.name = matched.name;
        currentUser.role = matched.role;
        document.getElementById('headerButtons').style.display = 'flex';
        showPage('services');
        updateBackButton();
        showNotification('Login successful!', 'success');
    } else {
        showNotification('Invalid username or password.', 'error');
    }
}

// File Upload
function handleFileUpload(event, type) {
    const files = Array.from(event.target.files);
    uploadedFiles[type] = uploadedFiles[type].concat(files);
    displayUploadedFiles(type);
}

function displayUploadedFiles(type) {
    const container = document.getElementById(type + 'Files');
    container.innerHTML = '';
    
    uploadedFiles[type].forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <span>${file.name} (${(file.size / 1024).toFixed(2)} KB)</span>
            <button class="file-remove" onclick="removeFile('${type}', ${index})">Remove</button>
        `;
        container.appendChild(fileItem);
    });
}

function removeFile(type, index) {
    uploadedFiles[type].splice(index, 1);
    displayUploadedFiles(type);
}

// Process Functions
function processCertification() {
    if (uploadedFiles.cert.length === 0) {
        alert('Please upload at least one file');
        return;
    }
    showPage('certTemplateView');
}

// Switch which form variant is visible (called by MNB classify result)
function showCertForm(cls) {
    const map = { '1A': 'form1A', '2A': 'form2A', '3A': 'form3A' };
    document.querySelectorAll('.lcr-form-variant').forEach(el => el.classList.remove('active-form'));
    const el = document.getElementById(map[cls] || 'form1A');
    if (el) el.classList.add('active-form');
}

function saveCertification() {
    if (confirm('Save certification and return to services?')) {
        alert('Certification saved successfully!');
        
        // Add record
        const newRecord = {
            id: 'BC-' + String(records.length + 1).padStart(3, '0'),
            type: 'birth',
            name: 'New Applicant',
            date: new Date().toISOString().split('T')[0],
            status: 'Pending'
        };
        records.push(newRecord);
        
        // Clear files and inputs
        uploadedFiles.cert = [];
        displayUploadedFiles('cert');
        document.getElementById('certFileInput').value = '';
        
        showPage('services');
    }
}

function processMarriage() {
    if (uploadedFiles.marriage.length === 0) {
        alert('Please upload at least one file');
        return;
    }
    showPage('marriageTemplateView');
}

function saveMarriage() {
    if (confirm('Save marriage license application and return to services?')) {
        alert('Marriage license application saved successfully!');
        
        // Add record
        const newRecord = {
            id: 'ML-' + String(records.length + 1).padStart(3, '0'),
            type: 'marriage-license',
            name: 'New Couple',
            date: new Date().toISOString().split('T')[0],
            status: 'Pending'
        };
        records.push(newRecord);
        
        // Clear files and inputs
        uploadedFiles.marriage = [];
        displayUploadedFiles('marriage');
        document.getElementById('marriageFileInput').value = '';
        
        showPage('services');
    }
}

// Records Management
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
    records = [
        { id: 'BC-001', type: 'birth',            name: 'Maria Santos',             date: '2025-01-10', status: 'Approved', formData: {} },
        { id: 'BC-002', type: 'birth',            name: 'Jose Reyes',               date: '2025-01-15', status: 'Pending',  formData: {} },
        { id: 'BC-003', type: 'birth',            name: 'Ana Dela Cruz',            date: '2025-02-03', status: 'Pending',  formData: {} },
        { id: 'DC-001', type: 'death',            name: 'Roberto Villanueva',       date: '2025-02-14', status: 'Approved', formData: {} },
        { id: 'DC-002', type: 'death',            name: 'Lourdes Magno',            date: '2025-03-01', status: 'Rejected', formData: {} },
        { id: 'MC-001', type: 'marriage-cert',    name: 'Carlos & Elena Bautista',  date: '2025-01-28', status: 'Approved', formData: {} },
        { id: 'MC-002', type: 'marriage-cert',    name: 'Ramon & Sofia Dizon',      date: '2025-02-20', status: 'Pending',  formData: {} },
        { id: 'ML-001', type: 'marriage-license', name: 'Paolo & Kristine Mendoza', date: '2025-03-05', status: 'Pending',  formData: {} },
        { id: 'ML-002', type: 'marriage-license', name: 'Angelo & Camille Torres',  date: '2025-03-06', status: 'Approved', formData: {} },
        { id: 'BC-004', type: 'birth',            name: 'Gabrielle Ramos',          date: '2025-03-07', status: 'Pending',  formData: {} }
    ];
    displayRecords(records);
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

// Drag and Drop functionality
document.addEventListener('DOMContentLoaded', function() {
    const uploadAreas = document.querySelectorAll('.upload-area');
    
    uploadAreas.forEach(area => {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            area.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            area.addEventListener(eventName, function() {
                this.style.borderColor = '#1ec77c';
                this.style.background = '#f0fdf7';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            area.addEventListener(eventName, function() {
                this.style.borderColor = '#999';
                this.style.background = 'white';
            }, false);
        });

        // Handle dropped files
        area.addEventListener('drop', function(e) {
            const files = e.dataTransfer.files;
            
            // Determine type based on ID
            let type = 'cert';
            if (this.id.includes('marriage') || this.parentElement.id.includes('marriage')) {
                type = 'marriage';
            }
            
            // Add files to array
            uploadedFiles[type] = uploadedFiles[type].concat(Array.from(files));
            displayUploadedFiles(type);
            
            // Update the file input
            const fileInput = document.getElementById(type + 'FileInput');
            if (fileInput) {
                const dt = new DataTransfer();
                uploadedFiles[type].forEach(file => dt.items.add(file));
                fileInput.files = dt.files;
            }
        }, false);
    });

    // Close user menu when clicking outside
    document.addEventListener('click', function(event) {
        const userMenu = document.getElementById('userMenu');
        const userIcon = document.querySelector('.user-icon');
        
        if (userMenu && userIcon && 
            !userMenu.contains(event.target) && 
            !userIcon.contains(event.target)) {
            closeUserMenu();
        }
        
        // Close modals when clicking outside
        const editModal = document.getElementById('editProfileModal');
        const passwordModal = document.getElementById('changePasswordModal');
        
        if (editModal && event.target === editModal) {
            closeEditProfileModal();
        }
        
        if (passwordModal && event.target === passwordModal) {
            closeChangePasswordModal();
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.altKey && e.key === 's' && isLoggedIn) {
            e.preventDefault();
            showPage('services');
        }
        if (e.altKey && e.key === 'r' && isLoggedIn) {
            e.preventDefault();
            showPage('records');
        }
        if (e.altKey && e.key === 'p' && isLoggedIn) {
            e.preventDefault();
            showPage('profile');
        }
        // Backspace or browser back for back button
        if (e.key === 'Backspace' && isLoggedIn && 
            !['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
            e.preventDefault();
            goBack();
        }
    });
});

// ============================================================
//  TEMPLATE EDIT / SAVE CHANGES / PRINT
// ============================================================
const _tplEditing = { cert: false, marriage: false };

function toggleTemplateEdit(ctx) {
    _tplEditing[ctx] = !_tplEditing[ctx];
    const box     = document.getElementById(ctx + 'TemplateBox');
    const editBtn = document.getElementById(ctx + 'EditBtn');
    const saveBtn = document.getElementById(ctx + 'SaveChangesBtn');

    if (_tplEditing[ctx]) {
        box.contentEditable = 'true';
        box.style.outline   = '2px dashed #1ec77c';
        box.style.minHeight = '80px';
        editBtn.textContent      = '✖ CANCEL';
        editBtn.style.background = '#aaa';
        saveBtn.style.display    = 'inline-flex';
    } else {
        box.contentEditable      = 'false';
        box.style.outline        = '';
        editBtn.textContent      = '✏️ EDIT';
        editBtn.style.background = '';
        saveBtn.style.display    = 'none';
    }
}

function saveTemplateChanges(ctx) {
    _tplEditing[ctx] = false;
    const box     = document.getElementById(ctx + 'TemplateBox');
    const editBtn = document.getElementById(ctx + 'EditBtn');
    const saveBtn = document.getElementById(ctx + 'SaveChangesBtn');
    box.contentEditable      = 'false';
    box.style.outline        = '';
    editBtn.textContent      = '✏️ EDIT';
    editBtn.style.background = '';
    saveBtn.style.display    = 'none';
    showNotification('Changes saved!', 'success');
}

function printTemplate(boxId) {
    const box = document.getElementById(boxId);
    if (!box) return;
    const win = window.open('', '_blank');
    win.document.write(`<!DOCTYPE html><html><head><title>Civil Registry Form</title>
        <style>
            body { font-family: 'Times New Roman', serif; margin: 60px; text-align: center; }
            .tbox { border: 1px solid #999; padding: 60px 40px; display: inline-block; font-size: 18px; min-width: 320px; }
        </style></head><body>
        <div class="tbox">${box.innerHTML}</div>
        </body></html>`);
    win.document.close();
    setTimeout(() => { win.print(); win.close(); }, 300);
}

// ============================================================
//  RECORD DETAIL MODAL — Official LCR Form Renderers
// ============================================================
let _currentRecord = null;
let _recordEditing = false;

function _field(key, placeholder, editMode, wide) {
    const d = (_currentRecord.formData) || {};
    const v = (d[key] !== undefined) ? d[key] : '';
    if (editMode) {
        return '<input class="lf-input' + (wide ? ' lf-input-wide' : '') + '" data-key="' + key + '" value="' + v + '" placeholder="' + (placeholder || '') + '">';
    }
    return '<span class="lf-val">' + v + '</span>';
}

function _statusField(editMode) {
    const s = _currentRecord.status;
    if (!editMode) return '<span class="lf-status lf-status-' + s.toLowerCase() + '">' + s + '</span>';
    return '<select class="lf-input lf-select" data-key="_status">' +
        '<option' + (s==='Pending'   ?' selected':'') + '>Pending</option>' +
        '<option' + (s==='Approved'  ?' selected':'') + '>Approved</option>' +
        '<option' + (s==='Rejected'  ?' selected':'') + '>Rejected</option>' +
        '<option' + (s==='Processed' ?' selected':'') + '>Processed</option>' +
        '</select>';
}

function viewRecord(record) {
    if (!record.formData) record.formData = {};
    _currentRecord = record;
    _recordEditing = false;
    document.getElementById('recordModalTitle').textContent = formatType(record.type) + ' — ' + record.name;
    document.getElementById('recordEditBtn').textContent    = '✏️ EDIT';
    document.getElementById('recordEditBtn').style.background = '';
    document.getElementById('recordSaveBtn').style.display  = 'none';
    renderRecordBody(false);
    document.getElementById('recordDetailModal').style.display = 'flex';
}

function renderRecordBody(editMode) {
    const type = _currentRecord.type;
    let html = '';
    if      (type === 'birth')            html = renderForm102(editMode);
    else if (type === 'death')            html = renderForm103(editMode);
    else if (type === 'marriage-cert')    html = renderForm97(editMode);
    else if (type === 'marriage-license') html = renderForm90(editMode);
    document.getElementById('recordModalBody').innerHTML = html;
}

// ── FORM 102 — CERTIFICATE OF LIVE BIRTH ─────────────────────
// ── FORM 102 — CERTIFICATE OF LIVE BIRTH ─────────────────────
function renderForm102(e) {
    const f = (k, p) => _field(k, p, e, false);
    const fw = (k, p) => _field(k, p, e, true);
    const hdr = '<div class="lcr-official-form">' +
        '<div class="lf-header-band">' +
            '<div class="lf-form-ref">Municipal Form No. 102<br><small>(Revised January 2007)</small></div>' +
            '<div class="lf-title-center">Republic of the Philippines<br>OFFICE OF THE CIVIL REGISTRAR GENERAL<br><strong>CERTIFICATE OF LIVE BIRTH</strong></div>' +
            '<div class="lf-reg-no">Registry No.<br>' + fw('registry_no','') + '</div>' +
        '</div>' +
        '<div class="lf-loc-row">' +
            '<div class="lf-loc-cell"><span class="lf-fn">Province</span>' + fw('province','') + '</div>' +
            '<div class="lf-loc-cell"><span class="lf-fn">City/Municipality</span>' + fw('city_municipality','') + '</div>' +
        '</div>';

    const child =
        '<div class="lf-section-label">CHILD</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">1. NAME — First</span>' + fw('child_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw('child_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw('child_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">2. SEX</span>' + f('sex','Male/Female') + '</td>' +
            '<td><span class="lf-fn">3. DATE OF BIRTH<br><small>Day / Month / Year</small></span>' +
                '<div class="lf-3col">' + f('dob_day','Day') + f('dob_month','Month') + f('dob_year','Year') + '</div></td>' +
            '<td><span class="lf-fn">6. WEIGHT AT BIRTH</span>' + f('weight','') + ' <small>grams</small></td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">4. PLACE OF BIRTH<br><small>Hospital/Clinic/Barangay</small></span>' + fw('pob_hospital','') + '</td>' +
            '<td><span class="lf-fn">City/Municipality</span>' + fw('pob_city','') + '</td>' +
            '<td><span class="lf-fn">Province</span>' + fw('pob_province','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">5a. TYPE OF BIRTH</span>' + f('type_of_birth','Single/Twin/etc.') + '</td>' +
            '<td><span class="lf-fn">5b. IF MULTIPLE BIRTH, CHILD WAS</span>' + f('birth_order','First/Second/etc.') + '</td>' +
            '<td><span class="lf-fn">5c. BIRTH ORDER</span>' + f('birth_order_total','e.g. First') + '</td>' +
        '</tr>' +
        '</table>';

    const mother =
        '<div class="lf-section-label">MOTHER</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">7. MAIDEN NAME — First</span>' + fw('mother_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw('mother_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw('mother_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">8. CITIZENSHIP</span>' + f('mother_citizenship','') + '</td>' +
            '<td><span class="lf-fn">9. RELIGION</span>' + f('mother_religion','') + '</td>' +
            '<td><span class="lf-fn">12. AGE AT TIME OF BIRTH</span>' + f('mother_age','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td colspan="2"><span class="lf-fn">13. RESIDENCE — House No., St., Barangay</span>' + fw('mother_address','') + '</td>' +
            '<td><span class="lf-fn">City/Municipality</span>' + fw('mother_city','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">Province</span>' + fw('mother_province','') + '</td>' +
            '<td><span class="lf-fn">10a. Total children born alive</span>' + f('mother_children_alive','') + '</td>' +
            '<td><span class="lf-fn">10b. Children still living</span>' + f('mother_children_living','') + '</td>' +
        '</tr>' +
        '</table>';

    const father =
        '<div class="lf-section-label">FATHER</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">14. NAME — First</span>' + fw('father_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw('father_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw('father_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">15. CITIZENSHIP</span>' + f('father_citizenship','') + '</td>' +
            '<td><span class="lf-fn">16. RELIGION</span>' + f('father_religion','') + '</td>' +
            '<td><span class="lf-fn">18. AGE AT TIME OF BIRTH</span>' + f('father_age','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td colspan="2"><span class="lf-fn">19. RESIDENCE — House No., St., Barangay</span>' + fw('father_address','') + '</td>' +
            '<td><span class="lf-fn">City/Municipality</span>' + fw('father_city','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">Province</span>' + fw('father_province','') + '</td>' +
            '<td><span class="lf-fn">17. OCCUPATION</span>' + f('father_occupation','') + '</td>' +
            '<td></td>' +
        '</tr>' +
        '</table>';

    const parents =
        '<div class="lf-section-label">MARRIAGE OF PARENTS</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">20a. DATE — Month</span>' + f('parents_marriage_month','') + '</td>' +
            '<td><span class="lf-fn">Day</span>' + f('parents_marriage_day','') + '</td>' +
            '<td><span class="lf-fn">Year</span>' + f('parents_marriage_year','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">20b. PLACE — City/Municipality</span>' + fw('parents_marriage_city','') + '</td>' +
            '<td><span class="lf-fn">Province</span>' + fw('parents_marriage_province','') + '</td>' +
            '<td><span class="lf-fn">Country</span>' + fw('parents_marriage_country','') + '</td>' +
        '</tr>' +
        '</table>';

    const status =
        '<div class="lf-section-label">RECORD STATUS</div>' +
        '<table class="lf-table"><tr>' +
            '<td><span class="lf-fn">Status</span>' + _statusField(e) + '</td>' +
            '<td><span class="lf-fn">Date Submitted</span>' + f('date_submitted','YYYY-MM-DD') + '</td>' +
            '<td><span class="lf-fn">Prepared By</span>' + f('prepared_by','') + '</td>' +
        '</tr></table></div>';

    return hdr + child + mother + father + parents + status;
}

// ── FORM 103 — CERTIFICATE OF DEATH ──────────────────────────
function renderForm103(e) {
    const f = (k, p) => _field(k, p, e, false);
    const fw = (k, p) => _field(k, p, e, true);
    const hdr =
        '<div class="lcr-official-form lf-plain">' +
        '<div class="lf-header-band">' +
            '<div class="lf-form-ref">Municipal Form No. 103<br><small>(Revised January 1993)</small></div>' +
            '<div class="lf-title-center">Republic of the Philippines<br>OFFICE OF THE CIVIL REGISTRAR GENERAL<br><strong>CERTIFICATE OF DEATH</strong></div>' +
            '<div class="lf-reg-no">Registry No.<br>' + fw('registry_no','') + '</div>' +
        '</div>' +
        '<div class="lf-loc-row">' +
            '<div class="lf-loc-cell"><span class="lf-fn">Province</span>' + fw('province','') + '</div>' +
            '<div class="lf-loc-cell"><span class="lf-fn">City/Municipality</span>' + fw('city_municipality','') + '</div>' +
        '</div>';

    const main =
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">1. NAME — First</span>' + fw('deceased_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw('deceased_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw('deceased_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">2. SEX</span>' + f('sex','Male/Female') + '</td>' +
            '<td><span class="lf-fn">3. RELIGION</span>' + f('religion','') + '</td>' +
            '<td><span class="lf-fn">4. AGE — Years / Months / Days</span>' +
                '<div class="lf-3col">' + f('age_years','Yrs') + f('age_months','Mo') + f('age_days','Days') + '</div></td>' +
        '</tr>' +
        '<tr>' +
            '<td colspan="2"><span class="lf-fn">5. PLACE OF DEATH — Hospital/Barangay</span>' + fw('pod_hospital','') + '</td>' +
            '<td><span class="lf-fn">City/Municipality</span>' + fw('pod_city','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">Province</span>' + fw('pod_province','') + '</td>' +
            '<td><span class="lf-fn">6. DATE OF DEATH — Day / Month / Year</span>' +
                '<div class="lf-3col">' + f('dod_day','Day') + f('dod_month','Month') + f('dod_year','Year') + '</div></td>' +
            '<td><span class="lf-fn">7. CITIZENSHIP</span>' + f('citizenship','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td colspan="2"><span class="lf-fn">8. RESIDENCE — House No., St., Barangay</span>' + fw('residence_address','') + '</td>' +
            '<td><span class="lf-fn">City/Municipality</span>' + fw('residence_city','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">Province</span>' + fw('residence_province','') + '</td>' +
            '<td><span class="lf-fn">9. CIVIL STATUS</span>' + f('civil_status','Single/Married/etc.') + '</td>' +
            '<td><span class="lf-fn">10. OCCUPATION</span>' + f('occupation','') + '</td>' +
        '</tr>' +
        '</table>';

    const causes =
        '<div class="lf-section-label">MEDICAL CERTIFICATE — CAUSES OF DEATH</div>' +
        '<table class="lf-table">' +
        '<tr><td><span class="lf-fn">17a. Immediate Cause</span>' + fw('cause_immediate','') + '</td></tr>' +
        '<tr><td><span class="lf-fn">17b. Antecedent Cause</span>' + fw('cause_antecedent','') + '</td></tr>' +
        '<tr><td><span class="lf-fn">17c. Underlying Cause</span>' + fw('cause_underlying','') + '</td></tr>' +
        '<tr><td><span class="lf-fn">17d. Other Significant Conditions Contributing to Death</span>' + fw('cause_other','') + '</td></tr>' +
        '</table>';

    const disposal =
        '<div class="lf-section-label">DISPOSAL</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">21. CORPSE DISPOSAL</span>' + f('corpse_disposal','Burial/Cremation') + '</td>' +
            '<td><span class="lf-fn">22. BURIAL/CREMATION PERMIT No.</span>' + f('burial_permit_no','') + '</td>' +
            '<td><span class="lf-fn">Date Issued</span>' + f('burial_permit_date','YYYY-MM-DD') + '</td>' +
            '<td><span class="lf-fn">23. AUTOPSY</span>' + f('autopsy','Yes/No') + '</td>' +
        '</tr>' +
        '<tr><td colspan="4"><span class="lf-fn">24. NAME AND ADDRESS OF CEMETERY/CREMATORY</span>' + fw('cemetery_address','') + '</td></tr>' +
        '</table>';

    const informant =
        '<div class="lf-section-label">INFORMANT</div>' +
        '<table class="lf-table"><tr>' +
            '<td><span class="lf-fn">Name in Print</span>' + fw('informant_name','') + '</td>' +
            '<td><span class="lf-fn">Relationship to Deceased</span>' + f('informant_relationship','') + '</td>' +
            '<td><span class="lf-fn">Address</span>' + fw('informant_address','') + '</td>' +
            '<td><span class="lf-fn">Date</span>' + f('informant_date','YYYY-MM-DD') + '</td>' +
        '</tr></table>';

    const status =
        '<div class="lf-section-label">RECORD STATUS</div>' +
        '<table class="lf-table"><tr>' +
            '<td><span class="lf-fn">Status</span>' + _statusField(e) + '</td>' +
            '<td><span class="lf-fn">Prepared By</span>' + f('prepared_by','') + '</td>' +
            '<td><span class="lf-fn">Date Received</span>' + f('date_received','YYYY-MM-DD') + '</td>' +
        '</tr></table></div>';

    return hdr + main + causes + disposal + informant + status;
}

// ── FORM 97 — CERTIFICATE OF MARRIAGE ────────────────────────
function renderForm97(e) {
    const f = (k, p) => _field(k, p, e, false);
    const fw = (k, p) => _field(k, p, e, true);

    const party = (label, px) =>
        '<div class="lf-section-label">' + label + '</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">1. NAME — First</span>' + fw(px+'_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw(px+'_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw(px+'_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">2a. Date of Birth — Day/Month/Year</span>' +
                '<div class="lf-3col">' + f(px+'_dob_day','Day') + f(px+'_dob_month','Month') + f(px+'_dob_year','Year') + '</div></td>' +
            '<td><span class="lf-fn">2b. Age</span>' + f(px+'_age','') + '</td>' +
            '<td><span class="lf-fn">3. Place of Birth — City/Municipality</span>' + fw(px+'_pob_city','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">Province</span>' + fw(px+'_pob_province','') + '</td>' +
            '<td><span class="lf-fn">4a. Sex</span>' + f(px+'_sex','Male/Female') + '</td>' +
            '<td><span class="lf-fn">4b. Citizenship</span>' + f(px+'_citizenship','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td colspan="2"><span class="lf-fn">5. Residence</span>' + fw(px+'_residence','') + '</td>' +
            '<td><span class="lf-fn">6. Religion</span>' + f(px+'_religion','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">7. Civil Status</span>' + f(px+'_civil_status','') + '</td>' +
            '<td><span class="lf-fn">8. Name of Father — First</span>' + fw(px+'_father_first','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw(px+'_father_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">9. Father\'s Citizenship</span>' + f(px+'_father_citizenship','') + '</td>' +
            '<td><span class="lf-fn">10. Maiden Name of Mother — First</span>' + fw(px+'_mother_first','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw(px+'_mother_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">11. Mother\'s Citizenship</span>' + f(px+'_mother_citizenship','') + '</td>' +
            '<td colspan="2"><span class="lf-fn">12. Name of Person Who Gave Consent — First</span>' + fw(px+'_consent_first','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">13. Relationship</span>' + f(px+'_consent_relationship','') + '</td>' +
            '<td colspan="2"><span class="lf-fn">14. Residence</span>' + fw(px+'_consent_residence','') + '</td>' +
        '</tr>' +
        '</table>';

    const hdr =
        '<div class="lcr-official-form lf-plain">' +
        '<div class="lf-header-band">' +
            '<div class="lf-form-ref">Municipal Form No. 97<br><small>(Revised January 2007)</small></div>' +
            '<div class="lf-title-center">Republic of the Philippines<br>OFFICE OF THE CIVIL REGISTRAR GENERAL<br><strong>CERTIFICATE OF MARRIAGE</strong></div>' +
            '<div class="lf-reg-no">Registry No.<br>' + fw('registry_no','') + '</div>' +
        '</div>' +
        '<div class="lf-loc-row">' +
            '<div class="lf-loc-cell"><span class="lf-fn">Province</span>' + fw('province','') + '</div>' +
            '<div class="lf-loc-cell"><span class="lf-fn">City/Municipality</span>' + fw('city_municipality','') + '</div>' +
        '</div>';

    const details =
        '<div class="lf-section-label">MARRIAGE DETAILS</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">15. Place of Marriage — Office/Church/Mosque</span>' + fw('marriage_venue','') + '</td>' +
            '<td><span class="lf-fn">City/Municipality</span>' + fw('marriage_city','') + '</td>' +
            '<td><span class="lf-fn">Province</span>' + fw('marriage_province','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">16. Date of Marriage — Day/Month/Year</span>' +
                '<div class="lf-3col">' + f('marriage_day','Day') + f('marriage_month','Month') + f('marriage_year','Year') + '</div></td>' +
            '<td><span class="lf-fn">17. Time of Marriage</span>' + f('marriage_time','e.g. 10:00 AM') + '</td>' +
            '<td></td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">Marriage License No.</span>' + f('license_no','') + '</td>' +
            '<td><span class="lf-fn">Date Issued</span>' + f('license_date_issued','YYYY-MM-DD') + '</td>' +
            '<td><span class="lf-fn">Place Issued</span>' + f('license_place_issued','') + '</td>' +
        '</tr>' +
        '</table>';

    const status =
        '<div class="lf-section-label">RECORD STATUS</div>' +
        '<table class="lf-table"><tr>' +
            '<td><span class="lf-fn">Status</span>' + _statusField(e) + '</td>' +
            '<td><span class="lf-fn">Received By</span>' + f('received_by','') + '</td>' +
            '<td><span class="lf-fn">Date Received</span>' + f('date_received','YYYY-MM-DD') + '</td>' +
        '</tr></table></div>';

    return hdr + party('HUSBAND', 'husband') + party('WIFE', 'wife') + details + status;
}

// ── FORM 90 — APPLICATION FOR MARRIAGE LICENSE ────────────────
function renderForm90(e) {
    const f = (k, p) => _field(k, p, e, false);
    const fw = (k, p) => _field(k, p, e, true);

    const applicant = (label, px) =>
        '<div class="lf-section-label">' + label + '</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">1. Name — First</span>' + fw(px+'_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw(px+'_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw(px+'_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">2. Date of Birth — Day/Month/Year</span>' +
                '<div class="lf-3col">' + f(px+'_dob_day','Day') + f(px+'_dob_month','Month') + f(px+'_dob_year','Year') + '</div></td>' +
            '<td><span class="lf-fn">Age</span>' + f(px+'_age','') + '</td>' +
            '<td><span class="lf-fn">3. Place of Birth — City/Municipality</span>' + fw(px+'_pob_city','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">Province</span>' + fw(px+'_pob_province','') + '</td>' +
            '<td><span class="lf-fn">4. Sex</span>' + f(px+'_sex','Male/Female') + '</td>' +
            '<td><span class="lf-fn">Citizenship</span>' + f(px+'_citizenship','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td colspan="2"><span class="lf-fn">5. Residence</span>' + fw(px+'_residence','') + '</td>' +
            '<td><span class="lf-fn">6. Religion</span>' + f(px+'_religion','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">7. Civil Status</span>' + f(px+'_civil_status','') + '</td>' +
            '<td><span class="lf-fn">8. If Previously Married — How Dissolved</span>' + f(px+'_prev_marriage','') + '</td>' +
            '<td><span class="lf-fn">11. Degree of Relationship</span>' + f(px+'_relationship_degree','None') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">12. Name of Father — First</span>' + fw(px+'_father_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw(px+'_father_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw(px+'_father_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">13. Father\'s Citizenship</span>' + f(px+'_father_citizenship','') + '</td>' +
            '<td colspan="2"><span class="lf-fn">14. Father\'s Residence</span>' + fw(px+'_father_residence','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">15. Maiden Name of Mother — First</span>' + fw(px+'_mother_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw(px+'_mother_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw(px+'_mother_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">16. Mother\'s Citizenship</span>' + f(px+'_mother_citizenship','') + '</td>' +
            '<td colspan="2"><span class="lf-fn">17. Mother\'s Residence</span>' + fw(px+'_mother_residence','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td colspan="3"><span class="lf-fn">18. Person Who Gave Consent/Advice</span>' + fw(px+'_consent_person','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">19. Relationship</span>' + f(px+'_consent_relationship','') + '</td>' +
            '<td><span class="lf-fn">20. Citizenship</span>' + f(px+'_consent_citizenship','') + '</td>' +
            '<td><span class="lf-fn">21. Residence</span>' + fw(px+'_consent_residence','') + '</td>' +
        '</tr>' +
        '</table>';

    const hdr =
        '<div class="lcr-official-form lf-plain">' +
        '<div class="lf-header-band">' +
            '<div class="lf-form-ref">Municipal Form 90 (Form No. 2)<br><small>(Revised January 2007)</small></div>' +
            '<div class="lf-title-center">Republic of the Philippines<br>OFFICE OF THE CIVIL REGISTRAR GENERAL<br><strong>APPLICATION FOR MARRIAGE LICENSE</strong></div>' +
            '<div class="lf-reg-no">Registry No.<br>' + fw('registry_no','') + '</div>' +
        '</div>' +
        '<div class="lf-loc-row">' +
            '<div class="lf-loc-cell"><span class="lf-fn">Province</span>' + fw('province','') + '</div>' +
            '<div class="lf-loc-cell"><span class="lf-fn">City/Municipality</span>' + fw('city_municipality','') + '</div>' +
        '</div>' +
        '<table class="lf-table"><tr>' +
            '<td><span class="lf-fn">Received by</span>' + fw('received_by','') + '</td>' +
            '<td><span class="lf-fn">Marriage License No.</span>' + f('license_no','') + '</td>' +
        '</tr><tr>' +
            '<td><span class="lf-fn">Date of Receipt</span>' + f('date_receipt','YYYY-MM-DD') + '</td>' +
            '<td><span class="lf-fn">Date of Issuance of Marriage License</span>' + f('date_issuance','YYYY-MM-DD') + '</td>' +
        '</tr></table>';

    const status =
        '<div class="lf-section-label">RECORD STATUS</div>' +
        '<table class="lf-table"><tr>' +
            '<td><span class="lf-fn">Status</span>' + _statusField(e) + '</td>' +
            '<td><span class="lf-fn">Processed By</span>' + f('processed_by','') + '</td>' +
            '<td><span class="lf-fn">Date Processed</span>' + f('date_processed','YYYY-MM-DD') + '</td>' +
        '</tr></table></div>';

    return hdr + applicant('GROOM', 'groom') + applicant('BRIDE', 'bride') + status;
}

function toggleRecordEdit() {
    _recordEditing = !_recordEditing;
    const editBtn = document.getElementById('recordEditBtn');
    const saveBtn = document.getElementById('recordSaveBtn');
    editBtn.textContent      = _recordEditing ? '✖ CANCEL' : '✏️ EDIT';
    editBtn.style.background = _recordEditing ? '#aaa' : '';
    saveBtn.style.display    = _recordEditing ? 'inline-flex' : 'none';
    renderRecordBody(_recordEditing);
}

// ── SAVE CHANGES ──────────────────────────────────────────────
function saveRecordChanges() {
    if (!_currentRecord.formData) _currentRecord.formData = {};
    document.querySelectorAll('#recordModalBody .lf-input').forEach(inp => {
        const key = inp.dataset.key;
        if (key === '_status') _currentRecord.status = inp.value;
        else _currentRecord.formData[key] = inp.value;
    });
    const idx = records.findIndex(r => r.id === _currentRecord.id);
    if (idx !== -1) records[idx] = { ..._currentRecord };
    displayRecords(records);
    _recordEditing = false;
    document.getElementById('recordEditBtn').textContent      = '✏️ EDIT';
    document.getElementById('recordEditBtn').style.background = '';
    document.getElementById('recordSaveBtn').style.display    = 'none';
    renderRecordBody(false);
    showNotification('Record updated successfully!', 'success');
}

// ── PRINT ─────────────────────────────────────────────────────
function printRecordModal() {
    const title   = document.getElementById('recordModalTitle').textContent;
    const content = document.getElementById('recordModalBody').innerHTML;
    const win = window.open('', '_blank');
    win.document.write('<!DOCTYPE html><html><head><title>' + title + '</title><style>' +
        '* { margin:0; padding:0; box-sizing:border-box; }' +
        'body { font-family: Arial, sans-serif; background:#fff; color:#111; padding:24px 32px; font-size:12px; }' +
        '.lf-input,.lf-select { display:none !important; }' +
        '.lf-val { display:inline-block; min-width:60px; border-bottom:1px solid #666; padding-bottom:1px; font-size:12px; }' +
        '.lf-status { padding:2px 8px; border-radius:3px; font-size:11px; font-weight:bold; display:inline-block; }' +
        '.lf-status-pending  { background:#fff3cd; color:#856404; }' +
        '.lf-status-approved { background:#d1e7dd; color:#0a3622; }' +
        '.lf-status-rejected { background:#f8d7da; color:#58151c; }' +
        '.lf-status-processed{ background:#cfe2ff; color:#084298; }' +
        '.lcr-official-form { border:2px solid #1a7a4a; width:100%; }' +
        '.lcr-official-form.lf-plain { border:2px solid #333; }' +
        '.lf-plain .lf-header-band { border-bottom:2px solid #333; }' +
        '.lf-plain .lf-reg-no { border:1.5px solid #333; }' +
        '.lf-plain .lf-loc-row { border-bottom:1.5px solid #333; }' +
        '.lf-plain .lf-loc-cell { border-right:1px solid #333; }' +
        '.lf-plain .lf-section-label { background:#2c3e50; }' +
        '.lf-plain .lf-table td,.lf-plain .lf-table th { border:1px solid #333; }' +
        '.lf-plain .lf-table th { background:#f0f0f0; color:#333; }' +
        '.lf-plain .lf-fn { color:#333; }' +
        '.lf-plain .lf-side-label { color:#333; }' +
        '.lf-header-band { display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2px solid #1a7a4a; padding:10px 12px; gap:10px; background:#fff; }' +
        '.lf-title-center { text-align:center; font-size:12px; flex:1; line-height:1.6; }' +
        '.lf-title-center strong { font-size:16px; display:block; margin-top:4px; letter-spacing:0.5px; }' +
        '.lf-form-ref { font-size:10px; color:#555; min-width:130px; }' +
        '.lf-reg-no { text-align:right; font-size:11px; border:1.5px solid #1a7a4a; padding:4px 10px; min-width:100px; }' +
        '.lf-loc-row { display:flex; border-bottom:1.5px solid #1a7a4a; }' +
        '.lf-loc-cell { flex:1; padding:5px 10px; font-size:12px; border-right:1px solid #1a7a4a; }' +
        '.lf-loc-cell:last-child { border-right:none; }' +
        '.lf-section-label { background:#1a7a4a; color:#fff; padding:4px 10px; font-size:11px; font-weight:bold; letter-spacing:0.5px; }' +
        '.lf-table { width:100%; border-collapse:collapse; }' +
        '.lf-table td,.lf-table th { border:1px solid #1a7a4a; padding:6px 8px; vertical-align:top; font-size:12px; }' +
        '.lf-table th { background:#e8f5f0; font-weight:bold; font-size:11px; text-align:center; color:#1a7a4a; }' +
        '.lf-fn { font-weight:bold; font-size:10px; color:#1a7a4a; display:block; margin-bottom:3px; }' +
        '.lf-sub { font-size:9px; color:#666; margin-right:2px; }' +
        '.lf-name-row { display:flex; flex-wrap:wrap; gap:6px; align-items:center; }' +
        '.lf-side-label { font-weight:bold; width:70px; font-size:11px; color:#1a7a4a; }' +
        '.lf-3col { display:flex; gap:8px; flex-wrap:nowrap; align-items:center; margin-top:3px; }' +
        '.lf-3col .lf-val { flex:1; min-width:0; }' +
        '.lf-table td { overflow:hidden; word-break:break-word; }' +
        '.lf-val { max-width:100%; word-break:break-word; }' +
        '</style></head><body>' + content + '</body></html>');
    win.document.close();
    setTimeout(() => { win.print(); win.close(); }, 500);
}

// ── CLOSE MODAL ───────────────────────────────────────────────
function closeRecordModal(e) {
    if (e && e.target !== document.getElementById('recordDetailModal')) return;
    document.getElementById('recordDetailModal').style.display = 'none';
    _currentRecord = null;
    _recordEditing = false;
}
