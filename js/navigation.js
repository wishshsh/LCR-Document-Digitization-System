// Update back button visibility
function updateBackButton() {
    const backButton = document.getElementById('backButton');
    const currentPage = navigationHistory[currentHistoryIndex];
    
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
        
        if (addToHistory) {
            navigationHistory = navigationHistory.slice(0, currentHistoryIndex + 1);
            navigationHistory.push(pageName);
            currentHistoryIndex = navigationHistory.length - 1;
        }
        
        updateBackButton();
        closeUserMenu();
    }

    if (pageName === 'records') {
        loadRecords();
    }
    
    if (pageName === 'profile') {
        updateProfilePage();
    }
}

// Home navigation
function goHome() {
    if (isLoggedIn) {
        showPage('services');
    }
}
