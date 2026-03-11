// ============================================================
//  EVENTS — DOMContentLoaded wiring: drag-drop, click-outside,
//           keyboard shortcuts
//  Load this LAST after all other js/ files
//  Depends on: globals.js, navigation.js, auth.js, uploads.js
// ============================================================

document.addEventListener('DOMContentLoaded', function () {

    // ── Drag-and-drop on upload areas ─────────────────────────
    document.querySelectorAll('.upload-area').forEach(area => {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev => {
            area.addEventListener(ev, e => { e.preventDefault(); e.stopPropagation(); }, false);
        });

        ['dragenter', 'dragover'].forEach(ev => {
            area.addEventListener(ev, function () {
                this.style.borderColor = '#1ec77c';
                this.style.background  = '#f0fdf7';
            }, false);
        });

        ['dragleave', 'drop'].forEach(ev => {
            area.addEventListener(ev, function () {
                this.style.borderColor = '#999';
                this.style.background  = 'white';
            }, false);
        });

        area.addEventListener('drop', function (e) {
            const type = (this.id.includes('marriage') || this.parentElement.id.includes('marriage'))
                ? 'marriage' : 'cert';

            uploadedFiles[type] = uploadedFiles[type].concat(Array.from(e.dataTransfer.files));
            displayUploadedFiles(type);

            const input = document.getElementById(type + 'FileInput');
            if (input) {
                const dt = new DataTransfer();
                uploadedFiles[type].forEach(f => dt.items.add(f));
                input.files = dt.files;
            }
        }, false);
    });

    // ── Click outside to close menus / modals ─────────────────
    document.addEventListener('click', function (event) {
        const userMenu = document.getElementById('userMenu');
        const userIcon = document.querySelector('.user-icon');
        if (userMenu && userIcon &&
            !userMenu.contains(event.target) &&
            !userIcon.contains(event.target)) {
            closeUserMenu();
        }

        const editModal     = document.getElementById('editProfileModal');
        const passwordModal = document.getElementById('changePasswordModal');
        if (editModal     && event.target === editModal)     closeEditProfileModal();
        if (passwordModal && event.target === passwordModal) closeChangePasswordModal();
    });

    // ── Keyboard shortcuts ────────────────────────────────────
    document.addEventListener('keydown', function (e) {
        if (e.altKey && e.key === 's' && isLoggedIn) { e.preventDefault(); showPage('services'); }
        if (e.altKey && e.key === 'r' && isLoggedIn) { e.preventDefault(); showPage('records');  }
        if (e.altKey && e.key === 'p' && isLoggedIn) { e.preventDefault(); showPage('profile');  }

        if (e.key === 'Backspace' && isLoggedIn &&
            !['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
            e.preventDefault();
            goBack();
        }
    });
});
