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

    const btn = document.querySelector('#certificationsPage .btn-proceed');
    btn.disabled     = true;
    btn.textContent  = 'Processing...';

    // Send each file through the pipeline
    // (for now just process the first file)
    const formData = new FormData();
    formData.append('file', uploadedFiles.cert[0]);
    formData.append('type', 'cert');

    fetch('php/process_upload.php', {
        method: 'POST',
        body:   formData          // multipart — no Content-Type header needed
    })
    .then(res => res.json())
    .then(data => {
        if (data.status !== 'success') {
            showNotification('Processing failed: ' + data.message, 'error');
            return;
        }

        // Switch to the correct form variant (1A, 2A, or 3A)
        showCertForm(data.form_class);

        // Pre-fill all extracted fields into the template form
        populateCertTemplate(data.form_class, data.fields);

        // Store doc_id so Save knows which DB record to update
        _pendingDocId = data.doc_id;

        showPage('certTemplateView');
        showNotification('Document processed successfully!', 'success');
    })
    .catch(() => {
        showNotification('Could not reach server. Is XAMPP running?', 'error');
    })
    .finally(() => {
        btn.disabled    = false;
        btn.textContent = 'PROCEED';
    });
}

// Fill the static template form spans with OCR-extracted values
function populateCertTemplate(formClass, fields) {
    const prefix = formClass === '1A' ? 'f1a' :
                   formClass === '2A' ? 'f2a' : 'f3a';

    // Map pipeline field names → template element IDs
    const fieldMap = {
        // Form 1A
        'registry_number':       prefix + '_registry',
        'date_of_registration':  prefix + '_date_reg',
        'child_name':            prefix + '_child_name',
        'sex':                   prefix + '_sex',
        'date_of_birth':         prefix + '_dob',
        'place_of_birth':        prefix + '_pob',
        'mother_name':           prefix + '_mother_name',
        'mother_nationality':    prefix + '_mother_nat',
        'father_name':           prefix + '_father_name',
        'father_nationality':    prefix + '_father_nat',
        'parents_marriage_date': prefix + '_marriage_date',
        'parents_marriage_place':prefix + '_marriage_place',
        // Form 2A
        'deceased_name':         prefix + '_deceased_name',
        'age':                   prefix + '_age',
        'civil_status':          prefix + '_civil_status',
        'nationality':           prefix + '_nationality',
        'date_of_death':         prefix + '_dod',
        'place_of_death':        prefix + '_pod',
        'cause_of_death':        prefix + '_cause',
        // Form 3A
        'date_of_marriage':      prefix + '_dom',
        'place_of_marriage':     prefix + '_pom',
        'husband_name':          prefix + '_husband_name',
        'wife_name':             prefix + '_wife_name',
    };

    Object.entries(fields).forEach(([key, value]) => {
        const elId = fieldMap[key];
        if (elId) {
            const el = document.getElementById(elId);
            if (el) el.textContent = value;
        }
    });
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
