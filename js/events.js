// Drag and Drop functionality + Global Event Listeners
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
            
            let type = 'cert';
            if (this.id.includes('marriage') || this.parentElement.id.includes('marriage')) {
                type = 'marriage';
            }
            
            uploadedFiles[type] = uploadedFiles[type].concat(Array.from(files));
            displayUploadedFiles(type);
            
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
        if (e.key === 'Backspace' && isLoggedIn && 
            !['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
            e.preventDefault();
            goBack();
        }
    });
});
