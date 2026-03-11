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
    if      (type === 'birth')            html = renderForm1A(editMode);
    else if (type === 'death')            html = renderForm2A(editMode);
    else if (type === 'marriage-cert')    html = renderForm3A(editMode);
    else if (type === 'marriage-license') html = renderForm3A(editMode);
    document.getElementById('recordModalBody').innerHTML = html;
}

// ============================================================
//  RECORD MODAL FORM RENDERERS — LCR Forms 1A / 2A / 3A
// ============================================================

// ── Shared helpers ────────────────────────────────────────────
// _field() and _statusField() defined above

// ── FORM 1A — CERTIFICATION OF BIRTH FACTS ───────────────────
function renderForm1A(e) {
    const f  = (k, p) => _field(k, p, e, false);
    const fw = (k, p) => _field(k, p, e, true);

    return `
    <div class="lcr-official-form lcr-form-1a">
        <div class="lf-cert-header">
            <div class="lf-cert-form-ref">LCR Form No. 1A<br><small>(Birth available)</small></div>
            <div class="lf-cert-title">
                <div>Republic of the Philippines</div>
                <div>Office of the City Registrar</div>
                <div>${fw('city', 'City/Municipality')}</div>
            </div>
            <div class="lf-cert-date-box">
                <span class="lf-fn">Date</span>
                ${fw('date', 'YYYY-MM-DD')}
            </div>
        </div>
        <div class="lf-cert-salutation">
            <strong>TO WHOM IT MAY CONCERN:</strong>
            <p>&emsp;We certify that, among others, the following facts of birth appear in our Registry of Births of this office:</p>
        </div>
        <div class="lf-cert-fields">
            <div class="lf-cert-row"><span class="lf-cert-label">Registry Number</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('registry_number', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date of Registration</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('date_of_registration', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Name of Child</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('child_name', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Sex</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${f('sex', 'Male / Female')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date of Birth</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('date_of_birth', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Place of Birth</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('place_of_birth', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Name of Mother</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('mother_name', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Nationality of Mother</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${f('mother_nationality', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Name of Father</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('father_name', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Nationality of Father</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${f('father_nationality', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date of Marriage of Parents</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('parents_marriage_date', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Place of Marriage of Parents</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('parents_marriage_place', '')}</span></div>
        </div>
        <div class="lf-cert-issuance">
            This certification is issued to ${fw('issued_to', 'Name of requesting party')} upon his/her request.
        </div>
        <div class="lf-cert-bottom">
            <div class="lf-cert-verified">
                <div class="lf-fn">Verified by:</div>
                <div class="lf-cert-sig-line">${fw('verified_by', '')}</div>
                <div class="lf-cert-sig-line">${fw('verified_position', '')}</div>
            </div>
            <div class="lf-cert-payment">
                <div class="lf-cert-pay-row"><span>Amount Paid</span><span>: ${f('amount_paid', '')}</span></div>
                <div class="lf-cert-pay-row"><span>OR Number</span><span>: ${f('or_number', '')}</span></div>
                <div class="lf-cert-pay-row"><span>Date Paid</span><span>: ${f('date_paid', '')}</span></div>
            </div>
        </div>
        <div class="lf-section-label">RECORD STATUS</div>
        <table class="lf-table"><tr>
            <td><span class="lf-fn">Status</span>${_statusField(e)}</td>
        </tr></table>
        <div class="lf-cert-note"><em>Note: A Mark, erasure or alteration of any entry invalidates this certification.</em></div>
    </div>`;
}

// ── FORM 2A — CERTIFICATION OF DEATH FACTS ───────────────────
function renderForm2A(e) {
    const f  = (k, p) => _field(k, p, e, false);
    const fw = (k, p) => _field(k, p, e, true);

    return `
    <div class="lcr-official-form lcr-form-2a">
        <div class="lf-cert-header">
            <div class="lf-cert-form-ref">LCR Form No. 2A<br><small>(Death available)</small></div>
            <div class="lf-cert-title">
                <div>Republic of the Philippines</div>
                <div>Office of the City Registrar</div>
                <div>${fw('city', 'City/Municipality')}</div>
            </div>
            <div class="lf-cert-date-box">
                <span class="lf-fn">Date</span>
                ${fw('date', 'YYYY-MM-DD')}
            </div>
        </div>
        <div class="lf-cert-salutation">
            <strong>TO WHOM IT MAY CONCERN:</strong>
            <p>&emsp;We certify that, among others, the following facts of death appear in our Registry of Deaths of this office:</p>
        </div>
        <div class="lf-cert-fields">
            <div class="lf-cert-row"><span class="lf-cert-label">Registry Number</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('registry_number', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date of Registration</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('date_of_registration', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Name of Deceased</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('deceased_name', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Sex</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${f('sex', 'Male / Female')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Age</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${f('age', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Civil Status</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${f('civil_status', 'Single / Married / etc.')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Nationality</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${f('nationality', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date of Death</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('date_of_death', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Place of Death</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('place_of_death', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Cause of Death</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('cause_of_death', '')}</span></div>
        </div>
        <div class="lf-cert-issuance">
            This certification is issued to ${fw('issued_to', 'Name of requesting party')} upon his/her request.
        </div>
        <div class="lf-cert-bottom">
            <div class="lf-cert-verified">
                <div class="lf-fn">Verified by:</div>
                <div class="lf-cert-sig-line">${fw('verified_by', '')}</div>
                <div class="lf-cert-sig-line">${fw('verified_position', '')}</div>
            </div>
            <div class="lf-cert-payment">
                <div class="lf-cert-pay-row"><span>Amount Paid</span><span>: ${f('amount_paid', '')}</span></div>
                <div class="lf-cert-pay-row"><span>OR Number</span><span>: ${f('or_number', '')}</span></div>
                <div class="lf-cert-pay-row"><span>Date Paid</span><span>: ${f('date_paid', '')}</span></div>
            </div>
        </div>
        <div class="lf-section-label">RECORD STATUS</div>
        <table class="lf-table"><tr>
            <td><span class="lf-fn">Status</span>${_statusField(e)}</td>
        </tr></table>
        <div class="lf-cert-note"><em>Note: A Mark, erasure or alteration of any entry invalidates this certification.</em></div>
    </div>`;
}

// ── FORM 3A — CERTIFICATION OF MARRIAGE FACTS ────────────────
function renderForm3A(e) {
    const f  = (k, p) => _field(k, p, e, false);
    const fw = (k, p) => _field(k, p, e, true);

    return `
    <div class="lcr-official-form lcr-form-3a">
        <div class="lf-cert-header">
            <div class="lf-cert-form-ref">LCR Form No. 3A<br><small>(Marriage available)</small></div>
            <div class="lf-cert-title">
                <div>Republic of the Philippines</div>
                <div>Office of the City Registrar</div>
                <div>${fw('city', 'City/Municipality')}</div>
            </div>
            <div class="lf-cert-date-box">
                <span class="lf-fn">Date</span>
                ${fw('date', 'YYYY-MM-DD')}
            </div>
        </div>
        <div class="lf-cert-salutation">
            <strong>TO WHOM IT MAY CONCERN:</strong>
            <p>&emsp;We certify that, among others, the following facts of marriage appear in our Registry of Marriages of this office:</p>
        </div>
        <div class="lf-cert-fields">
            <div class="lf-cert-row"><span class="lf-cert-label">Registry Number</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('registry_number', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date of Registration</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('date_of_registration', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date of Marriage</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('date_of_marriage', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Place of Marriage</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('place_of_marriage', '')}</span></div>
        </div>
        <table class="lf-table lf-cert-parties">
            <thead>
                <tr><th></th><th>HUSBAND</th><th>WIFE</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td class="lf-cert-row-label">Name</td>
                    <td>${fw('husband_name', '')}</td>
                    <td>${fw('wife_name', '')}</td>
                </tr>
                <tr>
                    <td class="lf-cert-row-label">Age</td>
                    <td>${f('husband_age', '')}</td>
                    <td>${f('wife_age', '')}</td>
                </tr>
                <tr>
                    <td class="lf-cert-row-label">Nationality</td>
                    <td>${f('husband_nationality', '')}</td>
                    <td>${f('wife_nationality', '')}</td>
                </tr>
                <tr>
                    <td class="lf-cert-row-label">Name of Mother</td>
                    <td>${fw('husband_mother_name', '')}</td>
                    <td>${fw('wife_mother_name', '')}</td>
                </tr>
                <tr>
                    <td class="lf-cert-row-label">Nationality of Mother</td>
                    <td>${f('husband_mother_nationality', '')}</td>
                    <td>${f('wife_mother_nationality', '')}</td>
                </tr>
                <tr>
                    <td class="lf-cert-row-label">Name of Father</td>
                    <td>${fw('husband_father_name', '')}</td>
                    <td>${fw('wife_father_name', '')}</td>
                </tr>
                <tr>
                    <td class="lf-cert-row-label">Nationality of Father</td>
                    <td>${f('husband_father_nationality', '')}</td>
                    <td>${f('wife_father_nationality', '')}</td>
                </tr>
            </tbody>
        </table>
        <div class="lf-cert-issuance">
            This certification is issued to ${fw('issued_to', 'Name of requesting party')} upon his/her request.
        </div>
        <div class="lf-cert-bottom">
            <div class="lf-cert-verified">
                <div class="lf-fn">Verified by:</div>
                <div class="lf-cert-sig-line">${fw('verified_by', '')}</div>
                <div class="lf-cert-sig-line">${fw('verified_position', '')}</div>
            </div>
            <div class="lf-cert-payment">
                <div class="lf-cert-pay-row"><span>Amount Paid</span><span>: ${f('amount_paid', '')}</span></div>
                <div class="lf-cert-pay-row"><span>OR Number</span><span>: ${f('or_number', '')}</span></div>
                <div class="lf-cert-pay-row"><span>Date Paid</span><span>: ${f('date_paid', '')}</span></div>
            </div>
        </div>
        <div class="lf-section-label">RECORD STATUS</div>
        <table class="lf-table"><tr>
            <td><span class="lf-fn">Status</span>${_statusField(e)}</td>
        </tr></table>
        <div class="lf-cert-note"><em>Note: A Mark, erasure or alteration of any entry invalidates this certification.</em></div>
    </div>`;
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
    win.document.write(`<!DOCTYPE html><html><head><title>${title}</title>
<style>
/* ── Reset & page ─────────────────────────────────────────── */
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: Arial, Helvetica, sans-serif;
    background: #fff;
    color: #111;
    padding: 32px 48px;
    font-size: 13px;
    line-height: 1.5;
}
@page { margin: 15mm 18mm; }

/* ── Hide inputs, show values as underlines ──────────────── */
.lf-input, .lf-select { display: none !important; }
.lf-val {
    display: inline-block;
    min-width: 120px;
    border-bottom: 1px solid #333;
    padding-bottom: 1px;
    font-size: 13px;
    word-break: break-word;
    vertical-align: bottom;
}

/* ── Status — plain text, no badge box ───────────────────── */
.lf-status { font-weight: bold; font-size: 13px; }
.lf-status-pending   { color: #856404; }
.lf-status-approved  { color: #0a3622; }
.lf-status-rejected  { color: #58151c; }
.lf-status-processed { color: #084298; }

/* ── Strip all box borders & backgrounds ─────────────────── */
.lcr-official-form,
.lcr-form-1a, .lcr-form-2a, .lcr-form-3a {
    border: none !important;
    background: transparent !important;
    width: 100%;
}

/* ── Hide RECORD STATUS section entirely ─────────────────── */
.lf-section-label,
.lf-table { display: none !important; }

/* ── Header: form ref top-left, title center, date top-right */
.lf-cert-header {
    display: block;
    border: none !important;
    padding: 0 0 18px 0;
    position: relative;
}
.lf-cert-form-ref {
    font-size: 11px;
    color: #333;
    line-height: 1.5;
    position: absolute;
    top: 0; left: 0;
}
.lf-cert-title {
    text-align: center;
    font-size: 13px;
    font-weight: normal;
    line-height: 1.8;
    padding: 0 130px;
}
.lf-cert-title div:nth-child(2) {
    font-size: 20px;
    font-weight: bold;
}
.lf-cert-date-box {
    position: absolute;
    top: 0; right: 0;
    font-size: 13px;
    text-align: right;
    display: flex;
    align-items: baseline;
    gap: 6px;
}
.lf-cert-date-box .lf-fn {
    display: inline;
    font-weight: normal;
    font-size: 13px;
    color: #111;
    margin: 0;
}
.lf-cert-date-box .lf-val { min-width: 120px; }

/* ── Salutation ──────────────────────────────────────────── */
.lf-cert-salutation {
    padding: 20px 0 10px 0;
    font-size: 13px;
    line-height: 1.7;
}
.lf-cert-salutation strong { font-size: 13px; }
.lf-cert-salutation p { margin-top: 6px; text-indent: 2em; }

/* ── Field rows ──────────────────────────────────────────── */
.lf-cert-fields { padding: 8px 0 16px 0; }
.lf-cert-row {
    display: flex;
    align-items: baseline;
    padding: 3px 0;
    border-bottom: none;
    gap: 0;
}
.lf-cert-label {
    min-width: 220px;
    flex-shrink: 0;
    font-size: 13px;
}
.lf-cert-colon {
    flex-shrink: 0;
    padding: 0 10px 0 4px;
}
.lf-cert-value {
    flex: 1;
}
.lf-cert-value .lf-val {
    width: 100%;
    min-width: 0;
    border-bottom: 1px solid #333;
    display: block;
}

/* ── Husband/Wife table (Form 3A) — plain grid ───────────── */
.lf-cert-parties {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 16px;
    table-layout: fixed;
}
.lf-cert-parties th {
    background: none !important;
    color: #111;
    text-align: center;
    padding: 5px 10px;
    font-size: 13px;
    font-weight: bold;
    border: 1px solid #999;
}
.lf-cert-parties td {
    border: 1px solid #999;
    padding: 5px 10px;
    font-size: 13px;
    vertical-align: middle;
}
.lf-cert-row-label {
    font-size: 12px;
    color: #333;
    background: none !important;
    width: 160px;
}
.lf-cert-parties .lf-val {
    display: block;
    width: 100%;
    border-bottom: 1px solid #555;
    min-width: 0;
}

/* ── Issuance line ───────────────────────────────────────── */
.lf-cert-issuance {
    padding: 16px 0;
    font-size: 13px;
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 6px;
    line-height: 2;
}
.lf-cert-issuance .lf-val {
    flex: 1;
    min-width: 200px;
    border-bottom: 1px solid #333;
}

/* ── Bottom: verified (left) + payment (left below) ─────── */
.lf-cert-bottom {
    display: block;
    padding: 16px 0;
    border-top: none;
}
.lf-cert-verified {
    font-size: 13px;
    margin-bottom: 32px;
}
.lf-cert-sig-line {
    display: inline-block;
    margin-top: 28px;
    border-bottom: 1px solid #333;
    min-width: 180px;
    padding-bottom: 1px;
}
.lf-cert-sig-line .lf-val {
    border-bottom: none;
    display: inline-block;
    min-width: 160px;
}
.lf-cert-payment {
    font-size: 13px;
    text-align: left;
    margin-top: 12px;
}
.lf-cert-pay-row {
    display: flex;
    align-items: baseline;
    gap: 0;
    padding: 3px 0;
}
.lf-cert-pay-row span:first-child { min-width: 110px; }
.lf-cert-pay-row span:nth-child(2) { padding: 0 8px; }
.lf-cert-pay-row .lf-val { min-width: 100px; border-bottom: 1px solid #333; }

/* ── Note ────────────────────────────────────────────────── */
.lf-cert-note {
    padding: 20px 0 0 0;
    font-size: 12px;
    color: #333;
    border-top: none;
    font-style: italic;
}
</style>
</head><body>${content}</body></html>`);
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