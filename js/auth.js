// ============================================================
//  AUTH — Login, logout, user menu, profile, password
//  Depends on: globals.js, navigation.js
// ============================================================

// ── Login → php/login.php ─────────────────────────────────────
function login(event) {
    event.preventDefault();
    const usernameInput = document.getElementById('username').value.trim();
    const passwordInput = document.getElementById('password').value;

    if (!usernameInput || !passwordInput) {
        showNotification('Please enter both username and password', 'error');
        return;
    }

    // Disable button while request is in-flight
    const btn = document.querySelector('#loginPage .btn-primary');
    if (btn) { btn.disabled = true; btn.textContent = 'Logging in...'; }

    fetch('php/login.php', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ username: usernameInput, password: passwordInput })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            isLoggedIn           = true;
            currentUser.username = data.user.name;
            currentUser.name     = data.user.name;
            currentUser.role     = data.user.role;
            currentUser.id       = data.user.id;
            document.getElementById('headerButtons').style.display = 'flex';
            showPage('services');
            updateBackButton();
            showNotification('Login successful!', 'success');
        } else {
            showNotification(data.message || 'Invalid username or password.', 'error');
        }
    })
    .catch(() => {
        showNotification('Could not reach the server. Is XAMPP running?', 'error');
    })
    .finally(() => {
        if (btn) { btn.disabled = false; btn.textContent = 'Login'; }
    });
}

// ── Logout ────────────────────────────────────────────────────
function logout() {
    closeUserMenu();
    if (confirm('Are you sure you want to logout?')) {
        isLoggedIn           = false;
        document.getElementById('headerButtons').style.display = 'none';
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
        uploadedFiles       = { cert: [], marriage: [] };
        navigationHistory   = ['login'];
        currentHistoryIndex = 0;
        currentUser.username = '';
        showPage('login', false);
        updateBackButton();
    }
}

// ── User menu ─────────────────────────────────────────────────
function toggleUserMenu() {
    const menu = document.getElementById('userMenu');
    if (menu.style.display === 'none' || menu.style.display === '') {
        menu.style.display = 'block';
        document.getElementById('userName').textContent  = currentUser.name;
        document.getElementById('userEmail').textContent = currentUser.email;
    } else {
        menu.style.display = 'none';
    }
}

function closeUserMenu() {
    document.getElementById('userMenu').style.display = 'none';
}

function viewProfile() {
    showPage('profile');
}

// ── Profile page ──────────────────────────────────────────────
function updateProfilePage() {
    document.getElementById('profileName').value       = currentUser.name;
    document.getElementById('profileEmail').value      = currentUser.email;
    document.getElementById('profileUsername').value   = currentUser.username;
    document.getElementById('profileRole').value       = currentUser.role;
    document.getElementById('profileDepartment').value = currentUser.department;
    document.getElementById('profileEmployeeId').value = currentUser.employeeId;
}

// ── Edit Profile modal ────────────────────────────────────────
function openEditProfileModal() {
    document.getElementById('editName').value       = currentUser.name;
    document.getElementById('editEmail').value      = currentUser.email;
    document.getElementById('editDepartment').value = currentUser.department;
    document.getElementById('editProfileModal').style.display = 'flex';
}

function closeEditProfileModal() {
    document.getElementById('editProfileModal').style.display = 'none';
    document.getElementById('editName').value       = '';
    document.getElementById('editEmail').value      = '';
    document.getElementById('editDepartment').value = '';
}

function saveProfileChanges(event) {
    event.preventDefault();
    currentUser.name       = document.getElementById('editName').value;
    currentUser.email      = document.getElementById('editEmail').value;
    currentUser.department = document.getElementById('editDepartment').value;
    updateProfilePage();
    document.getElementById('userName').textContent  = currentUser.name;
    document.getElementById('userEmail').textContent = currentUser.email;
    closeEditProfileModal();
    showNotification('Profile updated successfully!', 'success');
}

// ── Change Password modal ─────────────────────────────────────
function openChangePasswordModal() {
    document.getElementById('changePasswordModal').style.display = 'flex';
}

function closeChangePasswordModal() {
    document.getElementById('changePasswordModal').style.display = 'none';
    document.getElementById('currentPassword').value = '';
    document.getElementById('newPassword').value     = '';
    document.getElementById('confirmPassword').value = '';
}

function changePassword(event) {
    event.preventDefault();
    const newPassword     = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (newPassword !== confirmPassword) {
        showNotification('New passwords do not match!', 'error');
        return;
    }
    if (newPassword.length < 8) {
        showNotification('Password must be at least 8 characters long!', 'error');
        return;
    }
    closeChangePasswordModal();
    showNotification('Password changed successfully!', 'success');
}
