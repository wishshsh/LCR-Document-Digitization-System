// ============================================================
//  NAVIGATION — Page routing, back button, notifications
//  Depends on: globals.js
// ============================================================

function updateBackButton() {
    const backButton  = document.getElementById('backButton');
    const currentPage = navigationHistory[currentHistoryIndex];
    if (isLoggedIn && currentHistoryIndex > 0 && currentPage !== 'services') {
        backButton.style.display = 'flex';
    } else {
        backButton.style.display = 'none';
    }
}

function goBack() {
    if (currentHistoryIndex > 0) {
        currentHistoryIndex--;
        showPage(navigationHistory[currentHistoryIndex], false);
    }
}

function goHome() {
    if (isLoggedIn) showPage('services');
}

function showPage(pageName, addToHistory = true) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

    const target = document.getElementById(pageName + 'Page');
    if (target) {
        target.classList.add('active');

        if (addToHistory) {
            navigationHistory = navigationHistory.slice(0, currentHistoryIndex + 1);
            navigationHistory.push(pageName);
            currentHistoryIndex = navigationHistory.length - 1;
        }

        updateBackButton();
        closeUserMenu();
    }

    if (pageName === 'records') loadRecords();
    if (pageName === 'profile') updateProfilePage();
}

function showNotification(message, type) {
    const n = document.createElement('div');
    n.className   = `notification notification-${type}`;
    n.textContent = message;
    document.body.appendChild(n);

    setTimeout(() => n.classList.add('show'), 10);
    setTimeout(() => {
        n.classList.remove('show');
        setTimeout(() => document.body.removeChild(n), 300);
    }, 3000);
}
