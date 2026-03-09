// =============================================================
//  js/globals.js — Shared state, loaded FIRST before all others
// =============================================================

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
