// =============================================================
//  js/navigation.js — showPage, goBack, updateBackButton,
//                     goHome, showNotification
//  Requires: globals.js
// =============================================================

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
