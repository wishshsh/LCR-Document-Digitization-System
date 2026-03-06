// Global variables
let uploadedFiles = {
    cert: [],
    marriage: []
};

let records = [];

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

    fetch('php/login.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: usernameInput, password: passwordInput })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            isLoggedIn = true;
            
            // Update currentUser object with database info
            currentUser.username = data.user.name;
            currentUser.name = data.user.name; 
            currentUser.role = data.user.role;
            
            // Update UI
            document.getElementById('headerButtons').style.display = 'flex';
            showPage('services');
            updateBackButton();
            showNotification('Login successful!', 'success');
        } else {
            showNotification(data.message || 'Invalid credentials', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Server connection failed.', 'error');
    });
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
        
        // Map the database rows to match your frontend structure
        // This overwrites the global 'records' array so filtering still works
        records = data.map(dbRow => ({
            id: 'DOC-' + dbRow.doc_id, 
            type: dbRow.type_name.toLowerCase().replace(' ', '-'), // Rough mapping, adjust as needed
            name: dbRow.uploader_name,
            date: dbRow.upload_date.split(' ')[0], // Get just the YYYY-MM-DD part
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
