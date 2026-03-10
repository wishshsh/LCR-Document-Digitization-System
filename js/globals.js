// ============================================================
//  GLOBALS — Shared state across all modules
//  Load this FIRST before any other js/ file
// ============================================================

let uploadedFiles = {
    cert: [],
    marriage: []
};

let records = [];

// Navigation
let navigationHistory    = ['login'];
let currentHistoryIndex  = 0;
let isLoggedIn           = false;

// Current logged-in user
let currentUser = {
    username:   '',
    name:       'Admin User',
    email:      'admin@localregistry.gov.ph',
    role:       'Administrator',
    department: 'Civil Registry Office',
    employeeId: 'EMP-2024-001'
};

// Page URL map (for future deep-linking)
const pageUrls = {
    'login':                'https://localcivilregistry.gov.ph',
    'services':             'https://localcivilregistry.gov.ph/services',
    'certifications':       'https://localcivilregistry.gov.ph/services/certifications',
    'certTemplateView':     'https://localcivilregistry.gov.ph/services/certifications/template',
    'marriageLicense':      'https://localcivilregistry.gov.ph/services/marriage-license',
    'marriageTemplateView': 'https://localcivilregistry.gov.ph/services/marriage-license/template',
    'records':              'https://localcivilregistry.gov.ph/records',
    'profile':              'https://localcivilregistry.gov.ph/profile'
};
