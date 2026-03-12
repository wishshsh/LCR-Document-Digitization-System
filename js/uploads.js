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
    formData.append('type', 'marriage');

    fetch('php/process_upload.php', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.status !== 'success') {
                showNotification('Processing failed: ' + data.message, 'error');
                return;
            }

            _pendingDocId = data.doc_id;
            showCertForm(data.form_class);
            _populateFormTemplate(data.form_class, data.fields);

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
            status:   'Pending',
            formData: _collectTemplateFields('marriage')
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('Marriage license saved successfully!', 'success');
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