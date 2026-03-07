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
            
            currentUser.username = data.user.name;
            currentUser.name = data.user.name; 
            currentUser.role = data.user.role;
            
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
