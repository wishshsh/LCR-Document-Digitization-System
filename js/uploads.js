// =============================================================
//  js/uploads.js — file upload, drag-and-drop,
//                  process/save certification & marriage license
//  Requires: globals.js, navigation.js
// =============================================================

function handleFileUpload(event, type) {
    const files = Array.from(event.target.files);
    uploadedFiles[type] = uploadedFiles[type].concat(files);
    displayUploadedFiles(type);
}

function displayUploadedFiles(type) {
    const container = document.getElementById(type + 'Files');
    container.innerHTML = '';
    
    uploadedFiles[type].forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <span>${file.name} (${(file.size / 1024).toFixed(2)} KB)</span>
            <button class="file-remove" onclick="removeFile('${type}', ${index})">Remove</button>
        `;
        container.appendChild(fileItem);
    });
}

function removeFile(type, index) {
    uploadedFiles[type].splice(index, 1);
    displayUploadedFiles(type);
}

// Process Functions
function processCertification() {
    if (uploadedFiles.cert.length === 0) {
        alert('Please upload at least one file');
        return;
    }
    showPage('certTemplateView');
}

// Switch which form variant is visible (called by MNB classify result)
function showCertForm(cls) {
    const map = { '1A': 'form1A', '2A': 'form2A', '3A': 'form3A' };
    document.querySelectorAll('.lcr-form-variant').forEach(el => el.classList.remove('active-form'));
    const el = document.getElementById(map[cls] || 'form1A');
    if (el) el.classList.add('active-form');
}

function saveCertification() {
    if (confirm('Save certification and return to services?')) {
        alert('Certification saved successfully!');
        
        // Add record
        const newRecord = {
            id: 'BC-' + String(records.length + 1).padStart(3, '0'),
            type: 'birth',
            name: 'New Applicant',
            date: new Date().toISOString().split('T')[0],
            status: 'Pending'
        };
        records.push(newRecord);
        
        // Clear files and inputs
        uploadedFiles.cert = [];
        displayUploadedFiles('cert');
        document.getElementById('certFileInput').value = '';
        
        showPage('services');
    }
}

function processMarriage() {
    if (uploadedFiles.marriage.length === 0) {
        alert('Please upload at least one file');
        return;
    }
    showPage('marriageTemplateView');
}

function saveMarriage() {
    if (confirm('Save marriage license application and return to services?')) {
        alert('Marriage license application saved successfully!');
        
        // Add record
        const newRecord = {
            id: 'ML-' + String(records.length + 1).padStart(3, '0'),
            type: 'marriage-license',
            name: 'New Couple',
            date: new Date().toISOString().split('T')[0],
            status: 'Pending'
        };
        records.push(newRecord);
        
        // Clear files and inputs
        uploadedFiles.marriage = [];
        displayUploadedFiles('marriage');
        document.getElementById('marriageFileInput').value = '';
        
        showPage('services');
    }
}

// Records Management
