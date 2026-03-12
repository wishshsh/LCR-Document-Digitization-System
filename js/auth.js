// =============================================================
//  js/auth.js — login, logout, user menu, profile,
//               edit profile modal, change password modal
//  Requires: globals.js, navigation.js
// =============================================================

function login(event) {
    event.preventDefault();
    const usernameInput = document.getElementById('username').value;
    const passwordInput = document.getElementById('password').value;

    if (!usernameInput || !passwordInput) {
        showNotification('Please enter both username and password', 'error');
        return;
    }

    const loginBtn = document.querySelector('#loginForm button[type="submit"]') || document.getElementById('loginBtn');
    if (loginBtn) loginBtn.disabled = true;

    fetch('php/login.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: usernameInput, password: passwordInput })
    })
    .then(r => r.json())
    .then(data => {
        if (loginBtn) loginBtn.disabled = false;
        if (data.status === 'success') {
            isLoggedIn = true;
            currentUser.username = data.user.name;
            currentUser.name     = data.user.name;
            currentUser.role     = data.user.role;
            document.getElementById('headerButtons').style.display = 'flex';
            showPage('services');
            updateBackButton();
            showNotification('Login successful!', 'success');
        } else {
            showNotification(data.message || 'Invalid username or password', 'error');
        }
    })
    .catch(() => {
        if (loginBtn) loginBtn.disabled = false;
        showNotification('Cannot connect to server. Check that XAMPP is running.', 'error');
    });
}


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
