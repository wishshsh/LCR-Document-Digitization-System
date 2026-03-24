// ============================================================
//  UPLOADS — File upload, drag-and-drop, process & save
//  Depends on: globals.js, navigation.js, record-modal.js
// ============================================================

// Stores the doc_id returned by PHP after processing
let _pendingDocId = null;

// ── File input handlers ───────────────────────────────────────
function handleFileUpload(event, type) {
    const files = Array.from(event.target.files);
    uploadedFiles[type] = uploadedFiles[type].concat(files);
    displayUploadedFiles(type);
}

function displayUploadedFiles(type) {
    const container = document.getElementById(type + 'Files');
    container.innerHTML = '';
    uploadedFiles[type].forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <span>${file.name} (${(file.size / 1024).toFixed(2)} KB)</span>
            <button class="file-remove" onclick="removeFile('${type}', ${index})">Remove</button>
        `;
        container.appendChild(item);
    });
}

function removeFile(type, index) {
    uploadedFiles[type].splice(index, 1);
    displayUploadedFiles(type);
}

// ── CERTIFICATIONS — send to PHP → Flask pipeline ────────────
function processCertification() {
    if (uploadedFiles.cert.length === 0) {
        showNotification('Please upload at least one file.', 'error');
        return;
    }

    const btn = document.getElementById('certProceedBtn');
    _setProcessingState(btn, true, 'Processing...');

    const formData = new FormData();
    formData.append('file', uploadedFiles.cert[0]);
    formData.append('type', 'cert');

    fetch('php/process_upload.php', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.status !== 'success') {
                showNotification('Processing failed: ' + data.message, 'error');
                return;
            }

            // Store doc_id so saveCertification() knows which DB row to finalize
            _pendingDocId = data.doc_id;

            // Tell the template page which form variant to show (1A, 2A, or 3A)
            showCertForm(data.form_class);

            // Pre-fill all extracted fields into the form template
            _populateFormTemplate(data.form_class, data.fields);

            showPage('certTemplateView');
            showNotification('Document processed — please verify the extracted data.', 'success');
        })
        .catch(() => {
            showNotification('Could not reach server. Make sure XAMPP and Flask are running.', 'error');
        })
        .finally(() => {
            _setProcessingState(btn, false, 'PROCEED');
        });
}

// ── MARRIAGE LICENSE — same pipeline ─────────────────────────
function processMarriage() {
    if (uploadedFiles.marriage.length === 0) {
        showNotification('Please upload at least one file.', 'error');
        return;
    }

    const btn = document.getElementById('marriageProceedBtn');
    _setProcessingState(btn, true, 'Processing...');

    const formData = new FormData();
    formData.append('file', uploadedFiles.marriage[0]);
    formData.append('type', 'marriage-license');

    fetch('php/process_upload.php', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.status !== 'success') {
                showNotification('Processing failed: ' + data.message, 'error');
                return;
            }

            _pendingDocId = data.doc_id;
            _populateMarriageLicenseTemplate(data.fields || {});

            showPage('marriageTemplateView');
            showNotification('Document processed — please verify the extracted data.', 'success');
        })
        .catch(() => {
            showNotification('Could not reach server. Make sure XAMPP and Flask are running.', 'error');
        })
        .finally(() => {
            _setProcessingState(btn, false, 'PROCEED');
        });
}

// ── Switch which LCR form variant is visible ─────────────────
// Called automatically after pipeline returns form_class
function showCertForm(cls) {
    const map = { '1A': 'form1A', '2A': 'form2A', '3A': 'form3A' };
    document.querySelectorAll('.lcr-form-variant').forEach(el => el.classList.remove('active-form'));
    const el = document.getElementById(map[cls] || 'form1A');
    if (el) el.classList.add('active-form');
}

// ── Fill form template spans with NER-extracted values ────────
function _populateFormTemplate(formClass, fields) {
    const prefix = formClass === '1A' ? 'f1a'
                 : formClass === '2A' ? 'f2a'
                 : 'f3a';

    // Helper: assemble full name parts
    const join = (...parts) => parts.filter(Boolean).join(' ').trim();
    const date3 = (m, d, y) => [m, d ? d+',' : '', y].filter(Boolean).join(' ').trim();
    const place2 = (a, b) => [a, b].filter(Boolean).join(', ');

    // ── Assemble display values from granular DB fields ──────
    const assembled = {
        // Shared
        [prefix+'_city']:      fields['city_municipality']  || '',
        [prefix+'_date']:      fields['date_issuance']      || '',
        [prefix+'_registry']:  fields['registry_no']        || '',
        [prefix+'_date_reg']:  fields['date_submitted']     || fields['date_received'] || '',
        [prefix+'_issued_to']: fields['issued_to']          || '',
        [prefix+'_verified_by']:  fields['processed_by']    || '',
        [prefix+'_verified_pos']: fields['verified_position']|| '',
        [prefix+'_amount']:    fields['amount_paid']        || '',
        [prefix+'_or_number']: fields['or_number']          || '',
        [prefix+'_date_paid']: fields['date_paid']          || '',
    };

    if (formClass === '1A') {
        Object.assign(assembled, {
            'f1a_child_name':    join(fields['child_first'], fields['child_middle'], fields['child_last']),
            'f1a_sex':           fields['sex'] || '',
            'f1a_dob':           date3(fields['dob_month'], fields['dob_day'], fields['dob_year']),
            'f1a_pob':           place2(fields['pob_city'], fields['pob_province']),
            'f1a_mother_name':   join(fields['mother_first'], fields['mother_middle'], fields['mother_last']),
            'f1a_mother_nat':    fields['mother_citizenship'] || '',
            'f1a_father_name':   join(fields['father_first'], fields['father_middle'], fields['father_last']),
            'f1a_father_nat':    fields['father_citizenship'] || '',
            'f1a_marriage_date': date3(fields['parents_marriage_month'], fields['parents_marriage_day'], fields['parents_marriage_year']),
            'f1a_marriage_place':place2(fields['parents_marriage_city'], fields['parents_marriage_province']),
        });
    } else if (formClass === '2A') {
        Object.assign(assembled, {
            'f2a_deceased_name': join(fields['deceased_first'], fields['deceased_middle'], fields['deceased_last']),
            'f2a_sex':           fields['sex']          || '',
            'f2a_age':           fields['age_years']    || '',
            'f2a_civil_status':  fields['civil_status'] || '',
            'f2a_nationality':   fields['citizenship']  || '',
            'f2a_dod':           date3(fields['dod_month'], fields['dod_day'], fields['dod_year']),
            'f2a_pod':           place2(fields['pod_hospital'] || fields['pod_city'], fields['pod_province']),
            'f2a_cause':         fields['cause_immediate'] || '',
        });
    } else {
        // 3A — marriage cert uses husband_/wife_, license uses groom_/bride_
        const hFirst = fields['husband_first'] || fields['groom_first'] || '';
        const hMid   = fields['husband_middle']|| fields['groom_middle']|| '';
        const hLast  = fields['husband_last']  || fields['groom_last']  || '';
        const wFirst = fields['wife_first']    || fields['bride_first'] || '';
        const wMid   = fields['wife_middle']   || fields['bride_middle']|| '';
        const wLast  = fields['wife_last']     || fields['bride_last']  || '';
        Object.assign(assembled, {
            'f3a_dom':               date3(fields['marriage_month'], fields['marriage_day'], fields['marriage_year']),
            'f3a_pom':               place2(fields['marriage_venue'] || fields['marriage_city'], fields['marriage_province']),
            'f3a_husband_name':      join(hFirst, hMid, hLast),
            'f3a_husband_age':       fields['husband_age']    || fields['groom_age']    || '',
            'f3a_husband_nat':       fields['husband_citizenship'] || fields['groom_citizenship'] || '',
            'f3a_husband_mother':    join(fields['husband_mother_first'] || fields['groom_mother_first'], fields['husband_mother_last'] || fields['groom_mother_last']),
            'f3a_husband_mother_nat':fields['husband_mother_citizenship'] || fields['groom_mother_citizenship'] || '',
            'f3a_husband_father':    join(fields['husband_father_first'] || fields['groom_father_first'], fields['husband_father_last'] || fields['groom_father_last']),
            'f3a_husband_father_nat':fields['husband_father_citizenship'] || fields['groom_father_citizenship'] || '',
            'f3a_wife_name':         join(wFirst, wMid, wLast),
            'f3a_wife_age':          fields['wife_age']    || fields['bride_age']    || '',
            'f3a_wife_nat':          fields['wife_citizenship'] || fields['bride_citizenship'] || '',
            'f3a_wife_mother':       join(fields['wife_mother_first'] || fields['bride_mother_first'], fields['wife_mother_last'] || fields['bride_mother_last']),
            'f3a_wife_mother_nat':   fields['wife_mother_citizenship'] || fields['bride_mother_citizenship'] || '',
            'f3a_wife_father':       join(fields['wife_father_first'] || fields['bride_father_first'], fields['wife_father_last'] || fields['bride_father_last']),
            'f3a_wife_father_nat':   fields['wife_father_citizenship'] || fields['bride_father_citizenship'] || '',
        });
    }

    // ── Fill each span ────────────────────────────────────────
    console.log('_populateFormTemplate fields:', fields);
    console.log('_populateFormTemplate assembled:', assembled);
    Object.entries(assembled).forEach(([elId, value]) => {
        const el = document.getElementById(elId);
        if (!el || !value) return;
        el.textContent      = value;
        el.style.background = '#fffde7';
        el.style.borderBottom = '1px solid #f0d000';
    });
}

// ── SAVE CERTIFICATION (after user verifies the form) ─────────
function saveCertification() {
    if (!confirm('Save this certification to the database?')) return;

    fetch('php/save_record.php', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
            doc_id:   _pendingDocId,
            type:     _getCertificationType(),
            status:   'Pending',
            formData: _collectTemplateFields('cert')
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('Certification saved successfully!', 'success');
        } else {
            showNotification('Save failed: ' + data.message, 'error');
        }
    })
    .catch(() => {
        showNotification('Could not save. Is XAMPP running?', 'error');
    });

    // Reset and go back regardless
    _resetUpload('cert');
    _pendingDocId = null;
    showPage('services');
}

// ── SAVE MARRIAGE LICENSE ─────────────────────────────────────
function saveMarriage() {
    if (!confirm('Save this marriage license application to the database?')) return;

    fetch('php/save_record.php', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
            doc_id:   _pendingDocId,
            type:     'marriage-license',
            status:   'Submitted',
            formData: Object.assign(_normalizeMarriageFormData(_collectTemplateFields('marriage')), {
                workflow_stage: 'Form 90 Submitted',
                posting_status: 'Not Started',
                application_date: _currentDateISO(),
                form97_status: 'Awaiting Form 97',
                workflow_note: 'Marriage license workflow begins from the reviewed Form 90 application.'
            })
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('Marriage license application saved and added to the workflow.', 'success');
        } else {
            showNotification('Save failed: ' + data.message, 'error');
        }
    })
    .catch(() => {
        showNotification('Could not save. Is XAMPP running?', 'error');
    });

    _resetUpload('marriage');
    _pendingDocId = null;
    showPage('services');
}

// ── Helpers ───────────────────────────────────────────────────

// Collect all editable span values from the active template form
function _collectTemplateFields(type) {
    const formData = {};
    const container = document.getElementById(
        type === 'cert' ? 'certTemplateBox' : 'marriageTemplateBox'
    );
    if (!container) return formData;
    container.querySelectorAll('[id]').forEach(el => {
        // Element IDs follow the pattern f1a_*, f2a_*, f3a_*
        // Reverse-map them back to field keys using the same fieldMap
        formData[el.id] = el.textContent.trim();
    });
    return formData;
}



function _populateMarriageLicenseTemplate(fields) {
    const fieldMap = {
        f90_registry: 'registry_no',
        f90_province: 'province',
        f90_city: 'city_municipality',
        f90_received_by: 'received_by',
        f90_license_no: 'license_no',
        f90_date_receipt: 'date_received',
        f90_date_issuance: 'date_issuance',
        f90_groom_first: 'groom_first',
        f90_groom_middle: 'groom_middle',
        f90_groom_last: 'groom_last',
        f90_bride_first: 'bride_first',
        f90_bride_middle: 'bride_middle',
        f90_bride_last: 'bride_last',
        f90_groom_dob_day: 'groom_dob_day',
        f90_groom_dob_month: 'groom_dob_month',
        f90_groom_dob_year: 'groom_dob_year',
        f90_groom_age: 'groom_age',
        f90_bride_dob_day: 'bride_dob_day',
        f90_bride_dob_month: 'bride_dob_month',
        f90_bride_dob_year: 'bride_dob_year',
        f90_bride_age: 'bride_age',
        f90_groom_pob: 'groom_pob',
        f90_bride_pob: 'bride_pob',
        f90_groom_sex: 'groom_citizenship',
        f90_bride_sex: 'bride_citizenship',
        f90_groom_residence: 'groom_residence',
        f90_bride_residence: 'bride_residence',
        f90_groom_religion: 'groom_religion',
        f90_bride_religion: 'bride_religion',
        f90_groom_civil_status: 'groom_civil_status',
        f90_bride_civil_status: 'bride_civil_status',
        f90_groom_father_first: 'groom_father_first',
        f90_groom_father_middle: 'groom_father_middle',
        f90_groom_father_last: 'groom_father_last',
        f90_bride_father_first: 'bride_father_first',
        f90_bride_father_middle: 'bride_father_middle',
        f90_bride_father_last: 'bride_father_last',
        f90_groom_father_citizenship: 'groom_father_citizenship',
        f90_bride_father_citizenship: 'bride_father_citizenship',
        f90_groom_mother_first: 'groom_mother_first',
        f90_groom_mother_middle: 'groom_mother_middle',
        f90_groom_mother_last: 'groom_mother_last',
        f90_bride_mother_first: 'bride_mother_first',
        f90_bride_mother_middle: 'bride_mother_middle',
        f90_bride_mother_last: 'bride_mother_last',
        f90_groom_mother_citizenship: 'groom_mother_citizenship',
        f90_bride_mother_citizenship: 'bride_mother_citizenship'
    };

    Object.entries(fieldMap).forEach(([elementId, sourceKey]) => {
        const element = document.getElementById(elementId);
        if (!element) return;
        element.textContent = fields[sourceKey] || '';
    });
}

function _normalizeMarriageFormData(rawFields) {
    return {
        registry_no: rawFields.f90_registry || '',
        province: rawFields.f90_province || '',
        city_municipality: rawFields.f90_city || '',
        received_by: rawFields.f90_received_by || '',
        license_no: rawFields.f90_license_no || '',
        date_received: rawFields.f90_date_receipt || '',
        date_issuance: rawFields.f90_date_issuance || '',
        groom_first: rawFields.f90_groom_first || '',
        groom_middle: rawFields.f90_groom_middle || '',
        groom_last: rawFields.f90_groom_last || '',
        bride_first: rawFields.f90_bride_first || '',
        bride_middle: rawFields.f90_bride_middle || '',
        bride_last: rawFields.f90_bride_last || '',
        groom_dob_day: rawFields.f90_groom_dob_day || '',
        groom_dob_month: rawFields.f90_groom_dob_month || '',
        groom_dob_year: rawFields.f90_groom_dob_year || '',
        groom_age: rawFields.f90_groom_age || '',
        bride_dob_day: rawFields.f90_bride_dob_day || '',
        bride_dob_month: rawFields.f90_bride_dob_month || '',
        bride_dob_year: rawFields.f90_bride_dob_year || '',
        bride_age: rawFields.f90_bride_age || '',
        groom_pob: rawFields.f90_groom_pob || '',
        bride_pob: rawFields.f90_bride_pob || '',
        groom_citizenship: rawFields.f90_groom_sex || '',
        bride_citizenship: rawFields.f90_bride_sex || '',
        groom_residence: rawFields.f90_groom_residence || '',
        bride_residence: rawFields.f90_bride_residence || '',
        groom_religion: rawFields.f90_groom_religion || '',
        bride_religion: rawFields.f90_bride_religion || '',
        groom_civil_status: rawFields.f90_groom_civil_status || '',
        bride_civil_status: rawFields.f90_bride_civil_status || '',
        groom_father_first: rawFields.f90_groom_father_first || '',
        groom_father_middle: rawFields.f90_groom_father_middle || '',
        groom_father_last: rawFields.f90_groom_father_last || '',
        bride_father_first: rawFields.f90_bride_father_first || '',
        bride_father_middle: rawFields.f90_bride_father_middle || '',
        bride_father_last: rawFields.f90_bride_father_last || '',
        groom_father_citizenship: rawFields.f90_groom_father_citizenship || '',
        bride_father_citizenship: rawFields.f90_bride_father_citizenship || '',
        groom_mother_first: rawFields.f90_groom_mother_first || '',
        groom_mother_middle: rawFields.f90_groom_mother_middle || '',
        groom_mother_last: rawFields.f90_groom_mother_last || '',
        bride_mother_first: rawFields.f90_bride_mother_first || '',
        bride_mother_middle: rawFields.f90_bride_mother_middle || '',
        bride_mother_last: rawFields.f90_bride_mother_last || '',
        groom_mother_citizenship: rawFields.f90_groom_mother_citizenship || '',
        bride_mother_citizenship: rawFields.f90_bride_mother_citizenship || ''
    };
}

function _currentDateISO() {
    return new Date().toISOString().slice(0, 10);
}

function _getCertificationType() {
    const activeForm = document.querySelector('#certTemplateBox .lcr-form-variant.active-form');
    if (!activeForm) return 'birth';
    if (activeForm.id === 'form2A') return 'death';
    if (activeForm.id === 'form3A') return 'marriage-cert';
    return 'birth';
}

function _resetUpload(type) {
    uploadedFiles[type] = [];
    displayUploadedFiles(type);
    const input = document.getElementById(type + 'FileInput');
    if (input) input.value = '';
}

function _setProcessingState(btn, loading, label) {
    if (!btn) return;
    btn.disabled    = loading;
    btn.textContent = label;
    btn.style.opacity = loading ? '0.7' : '1';
}