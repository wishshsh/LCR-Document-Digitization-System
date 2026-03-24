// ============================================================
//  RECORD MODAL — View, edit, save, print, close
//  Depends on: globals.js, navigation.js, records.js,
//              forms/form-1a.js, forms/form-2a.js, forms/form-3a.js
// ============================================================

let _currentRecord = null;
let _recordEditing = false;

// ── Field helpers (used by form renderers) ────────────────────
function _field(key, placeholder, editMode, wide) {
    const v = (_currentRecord.formData || {})[key] || '';
    if (editMode) {
        return `<input class="lf-input${wide ? ' lf-input-wide' : ''}" data-key="${key}" value="${v}" placeholder="${placeholder || ''}">`;
    }
    return `<span class="lf-val">${v}</span>`;
}

function _statusField(editMode) {
    const s = _currentRecord.status;
    if (!editMode) return `<span class="lf-status lf-status-${s.toLowerCase()}">${s}</span>`;
    return `<select class="lf-input lf-select" data-key="_status">
        <option${s === 'Submitted' ? ' selected' : ''}>Submitted</option>
        <option${s === 'For Posting' ? ' selected' : ''}>For Posting</option>
        <option${s === 'Eligible for License' ? ' selected' : ''}>Eligible for License</option>
        <option${s === 'License Issued' ? ' selected' : ''}>License Issued</option>
        <option${s === 'Marriage Registered' ? ' selected' : ''}>Marriage Registered</option>
        <option${s === 'Pending'   ? ' selected' : ''}>Pending</option>
        <option${s === 'Approved'  ? ' selected' : ''}>Approved</option>
        <option${s === 'Rejected'  ? ' selected' : ''}>Rejected</option>
        <option${s === 'Processed' ? ' selected' : ''}>Processed</option>
    </select>`;
}

// ── Open modal ────────────────────────────────────────────────
function viewRecord(record) {
    if (!record.formData) record.formData = {};
    _currentRecord = record;
    _recordEditing = false;

    document.getElementById('recordModalTitle').textContent      = formatType(record.type) + ' — ' + record.name;
    document.getElementById('recordEditBtn').textContent         = '✏️ EDIT';
    document.getElementById('recordEditBtn').style.background    = '';
    document.getElementById('recordSaveBtn').style.display       = 'none';
    renderRecordBody(false);
    document.getElementById('recordDetailModal').style.display   = 'flex';
}

// ── Render body (dispatches to correct form renderer) ─────────
function renderRecordBody(editMode) {
    const type = _currentRecord.type;
    let html = '';
    if      (type === 'birth')            html = renderForm1A(editMode);
    else if (type === 'death')            html = renderForm2A(editMode);
    else if (type === 'marriage-cert')    html = renderForm3A(editMode);
    else if (type === 'marriage-license') html = renderMarriageLicenseWorkflow(editMode);
    document.getElementById('recordModalBody').innerHTML = html;
}

// ── Toggle edit mode ──────────────────────────────────────────
function toggleRecordEdit() {
    _recordEditing = !_recordEditing;
    const editBtn  = document.getElementById('recordEditBtn');
    const saveBtn  = document.getElementById('recordSaveBtn');
    editBtn.textContent      = _recordEditing ? '✖ CANCEL' : '✏️ EDIT';
    editBtn.style.background = _recordEditing ? '#aaa'     : '';
    saveBtn.style.display    = _recordEditing ? 'inline-flex' : 'none';
    renderRecordBody(_recordEditing);
}

// ── Save changes ──────────────────────────────────────────────


function _marriageValue(...keys) {
    const data = _currentRecord.formData || {};
    for (const key of keys) {
        const value = data[key];
        if (value !== undefined && value !== null && String(value).trim() !== '') {
            return String(value);
        }
    }
    return '';
}

function _marriageInput(key, placeholder, editMode, wide, ...fallbackKeys) {
    const value = _marriageValue(key, ...fallbackKeys);
    if (editMode) {
        return `<input class="lf-input${wide ? ' lf-input-wide' : ''}" data-key="${key}" value="${value}" placeholder="${placeholder || ''}">`;
    }
    return `<span class="lf-val">${value}</span>`;
}

function _marriageNameField(prefix, editMode) {
    if (editMode) {
        return `<div class="lf-3col marriage-name-edit">
            <input class="lf-input" data-key="${prefix}_first" value="${_marriageValue(prefix + '_first')}" placeholder="First">
            <input class="lf-input" data-key="${prefix}_middle" value="${_marriageValue(prefix + '_middle')}" placeholder="Middle">
            <input class="lf-input" data-key="${prefix}_last" value="${_marriageValue(prefix + '_last')}" placeholder="Last">
        </div>`;
    }
    return `<span class="lf-val">${[
        _marriageValue(prefix + '_first'),
        _marriageValue(prefix + '_middle'),
        _marriageValue(prefix + '_last')
    ].filter(Boolean).join(' ')}</span>`;
}

function _marriageBirthField(prefix, editMode) {
    if (editMode) {
        return `<div class="lf-3col marriage-birth-edit">
            <input class="lf-input" data-key="${prefix}_dob_day" value="${_marriageValue(prefix + '_dob_day')}" placeholder="Day">
            <input class="lf-input" data-key="${prefix}_dob_month" value="${_marriageValue(prefix + '_dob_month')}" placeholder="Month">
            <input class="lf-input" data-key="${prefix}_dob_year" value="${_marriageValue(prefix + '_dob_year')}" placeholder="Year">
            <input class="lf-input" data-key="${prefix}_age" value="${_marriageValue(prefix + '_age')}" placeholder="Age">
        </div>`;
    }
    const parts = [
        _marriageValue(prefix + '_dob_day'),
        _marriageValue(prefix + '_dob_month'),
        _marriageValue(prefix + '_dob_year')
    ].filter(Boolean).join(' / ');
    const age = _marriageValue(prefix + '_age');
    return `<span class="lf-val">${parts}${age ? ` (Age: ${age})` : ''}</span>`;
}

function renderMarriageLicenseDocument(editMode) {
    return `
    <div class="marriage-license-document lcr-official-form lf-plain">
        <div class="lf-cert-header marriage-license-header">
            <div class="lf-cert-form-ref">Municipal Form 90<br><small>Marriage License Record</small></div>
            <div class="lf-cert-title">
                <div>Republic of the Philippines</div>
                <div>OFFICE OF THE CIVIL REGISTRAR GENERAL</div>
                <div>${_marriageInput('city_municipality', 'City/Municipality', editMode, true, 'city')}</div>
            </div>
            <div class="lf-cert-date-box">
                <span class="lf-fn">Issued</span>
                ${_marriageInput('date_issuance', 'YYYY-MM-DD', editMode, false, 'license_issue_date', 'date')}
            </div>
        </div>

        <div class="marriage-license-banner">
            <div class="marriage-license-title">MARRIAGE LICENSE</div>
            <p>This document is prepared from the approved Form 90 application and may be updated for issuance or printing by the Local Civil Registry staff.</p>
        </div>

        <div class="lf-cert-fields marriage-license-meta">
            <div class="lf-cert-row"><span class="lf-cert-label">Registry Number</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${_marriageInput('registry_no', 'Registry Number', editMode, true, 'registry_number')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Marriage License Number</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${_marriageInput('license_no', 'License Number', editMode, true)}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Province</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${_marriageInput('province', 'Province', editMode, true)}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">City / Municipality</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${_marriageInput('city_municipality', 'City/Municipality', editMode, true, 'city')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date Received</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${_marriageInput('date_received', 'YYYY-MM-DD', editMode, false, 'date_of_registration', 'application_date')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Valid Until</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${_marriageInput('license_expiry_date', 'YYYY-MM-DD', editMode, false)}</span></div>
        </div>

        <table class="lf-table marriage-license-parties">
            <thead>
                <tr><th>Field</th><th>Groom</th><th>Bride</th></tr>
            </thead>
            <tbody>
                <tr><td class="lf-cert-row-label">Applicant Name</td><td>${_marriageNameField('groom', editMode)}</td><td>${_marriageNameField('bride', editMode)}</td></tr>
                <tr><td class="lf-cert-row-label">Date of Birth / Age</td><td>${_marriageBirthField('groom', editMode)}</td><td>${_marriageBirthField('bride', editMode)}</td></tr>
                <tr><td class="lf-cert-row-label">Place of Birth</td><td>${_marriageInput('groom_pob', 'Place of Birth', editMode, true)}</td><td>${_marriageInput('bride_pob', 'Place of Birth', editMode, true)}</td></tr>
                <tr><td class="lf-cert-row-label">Citizenship</td><td>${_marriageInput('groom_citizenship', 'Citizenship', editMode, false, 'husband_nationality')}</td><td>${_marriageInput('bride_citizenship', 'Citizenship', editMode, false, 'wife_nationality')}</td></tr>
                <tr><td class="lf-cert-row-label">Residence</td><td>${_marriageInput('groom_residence', 'Residence', editMode, true)}</td><td>${_marriageInput('bride_residence', 'Residence', editMode, true)}</td></tr>
                <tr><td class="lf-cert-row-label">Religion / Sect</td><td>${_marriageInput('groom_religion', 'Religion / Sect', editMode, false)}</td><td>${_marriageInput('bride_religion', 'Religion / Sect', editMode, false)}</td></tr>
                <tr><td class="lf-cert-row-label">Civil Status</td><td>${_marriageInput('groom_civil_status', 'Civil Status', editMode, false)}</td><td>${_marriageInput('bride_civil_status', 'Civil Status', editMode, false)}</td></tr>
                <tr><td class="lf-cert-row-label">Name of Father</td><td>${_marriageNameField('groom_father', editMode)}</td><td>${_marriageNameField('bride_father', editMode)}</td></tr>
                <tr><td class="lf-cert-row-label">Father Citizenship</td><td>${_marriageInput('groom_father_citizenship', 'Citizenship', editMode, false)}</td><td>${_marriageInput('bride_father_citizenship', 'Citizenship', editMode, false)}</td></tr>
                <tr><td class="lf-cert-row-label">Maiden Name of Mother</td><td>${_marriageNameField('groom_mother', editMode)}</td><td>${_marriageNameField('bride_mother', editMode)}</td></tr>
                <tr><td class="lf-cert-row-label">Mother Citizenship</td><td>${_marriageInput('groom_mother_citizenship', 'Citizenship', editMode, false)}</td><td>${_marriageInput('bride_mother_citizenship', 'Citizenship', editMode, false)}</td></tr>
            </tbody>
        </table>

        <div class="marriage-license-certification">
            <p>This license is issued after completion of the required review and posting period, with no legal impediment recorded by this office.</p>
            <p><strong>Workflow Note:</strong> ${_marriageInput('workflow_note', 'Add note for the issued license', editMode, true)}</p>
        </div>

        <div class="marriage-license-footer">
            <div class="marriage-license-signature-block">
                <div class="marriage-license-signature-line">${_marriageInput('received_by', 'Received / Prepared by', editMode, true)}</div>
                <div class="marriage-license-signature-label">Prepared / Received by</div>
            </div>
            <div class="marriage-license-signature-block">
                <div class="marriage-license-signature-line">${_marriageInput('civil_registrar_name', 'Civil Registrar', editMode, true)}</div>
                <div class="marriage-license-signature-label">Civil Registrar</div>
            </div>
        </div>
    </div>`;
}

function renderMarriageLicenseWorkflow(editMode) {
    const data = _currentRecord.formData || {};
    const stage = data.workflow_stage || 'Form 90 Submitted';
    const postingStatus = data.posting_status || 'Not Started';
    const form97Status = data.form97_status || 'Awaiting Form 97';

    return `
    <div class="marriage-workflow-panel">
        <div class="marriage-workflow-header">
            <div>
                <h4 class="marriage-workflow-title">Marriage License Workflow</h4>
                <p class="marriage-workflow-subtitle">Tracks the Form 90 application, posting period, license issuance, and Form 97 registration.</p>
            </div>
            <span class="marriage-stage-pill">${stage}</span>
        </div>
        <div class="marriage-stage-grid">
            <div class="marriage-stage-card"><strong>Application</strong><span>Filed on ${data.application_date || data.date_received || 'Not set'}<br>Status: ${_currentRecord.status}</span></div>
            <div class="marriage-stage-card"><strong>Posting</strong><span>${postingStatus}<br>${data.posting_start_date || 'No posting start date'} to ${data.posting_end_date || 'No posting end date'}</span></div>
            <div class="marriage-stage-card"><strong>License</strong><span>No.: ${data.license_no || 'Pending generation'}<br>Issued: ${data.license_issue_date || data.date_issuance || 'Not issued'}<br>Valid until: ${data.license_expiry_date || 'Not available'}</span></div>
            <div class="marriage-stage-card"><strong>Form 97 / Form 3A</strong><span>${form97Status}<br>Received: ${data.form97_received_date || 'Not received'}<br>Processed: ${data.form97_processed_date || 'Not processed'}</span></div>
        </div>
        <div class="marriage-workflow-actions">
            <button class="marriage-workflow-btn posting" onclick="advanceMarriageWorkflow('start-posting')">Start 10-Day Posting</button>
            <button class="marriage-workflow-btn eligible" onclick="advanceMarriageWorkflow('mark-eligible')">Mark Eligible for License</button>
            <button class="marriage-workflow-btn issue" onclick="advanceMarriageWorkflow('issue-license')">Issue Marriage License</button>
            <button class="marriage-workflow-btn register" onclick="advanceMarriageWorkflow('register-form97')">Register Form 97 to Form 3A</button>
            <button class="marriage-workflow-btn print" onclick="printMarriageLicenseCertificate()">Print Marriage License</button>
        </div>
    </div>

    ${renderMarriageLicenseDocument(editMode)}`;
}

function advanceMarriageWorkflow(action) {
    if (!_currentRecord || _currentRecord.type !== 'marriage-license') return;
    const data = _currentRecord.formData || (_currentRecord.formData = {});
    const today = _workflowDate(0);

    if (action === 'start-posting') {
        data.workflow_stage = '10-Day Posting';
        data.posting_status = 'Posting Started';
        data.posting_start_date = today;
        data.posting_end_date = data.posting_end_date || _workflowDate(10);
        _currentRecord.status = 'For Posting';
        data.workflow_note = 'Application is now under the mandatory 10-day public posting period.';
    } else if (action === 'mark-eligible') {
        data.workflow_stage = 'Eligible for License';
        data.posting_status = 'Posting Completed';
        data.posting_end_date = data.posting_end_date || today;
        _currentRecord.status = 'Eligible for License';
        data.workflow_note = 'Posting completed with no legal objection recorded.';
    } else if (action === 'issue-license') {
        data.workflow_stage = 'Marriage License Issued';
        data.license_issue_date = today;
        data.date_issuance = today;
        data.date = today;
        data.license_expiry_date = _workflowDate(120);
        data.license_no = data.license_no || _generateMarriageLicenseNumber();
        _currentRecord.status = 'License Issued';
        data.workflow_note = 'Marriage License has been issued and is valid for 120 days.';
    } else if (action === 'register-form97') {
        data.workflow_stage = 'Form 97 Registered to Form 3A';
        data.form97_status = 'Scanned and Mapped to Form 3A';
        data.form97_received_date = data.form97_received_date || today;
        data.form97_processed_date = today;
        _currentRecord.status = 'Marriage Registered';
        data.workflow_note = 'Signed Form 97 received and processed for the permanent marriage record.';
    }

    const idx = records.findIndex(r => r.id === _currentRecord.id);
    if (idx !== -1) records[idx] = { ..._currentRecord };
    displayRecords(records);
    renderRecordBody(false);
    persistMarriageWorkflow();
}

function persistMarriageWorkflow() {
    fetch('php/save_record.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            doc_id: _currentRecord.doc_id,
            status: _currentRecord.status,
            formData: _currentRecord.formData
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') showNotification('Marriage workflow updated.', 'success');
        else showNotification('Workflow update failed: ' + (data.message || 'Unknown error'), 'error');
    })
    .catch(() => {
        showNotification('Could not reach server while updating workflow.', 'error');
    });
}

function _workflowDate(offsetDays) {
    const date = new Date();
    date.setDate(date.getDate() + offsetDays);
    return date.toISOString().slice(0, 10);
}

function _generateMarriageLicenseNumber() {
    return 'ML-' + new Date().toISOString().slice(0, 10).replace(/-/g, '') + '-' + String(_currentRecord.doc_id).padStart(4, '0');
}

function printMarriageLicenseCertificate() {
    if (!_currentRecord || _currentRecord.type !== 'marriage-license') return;

    const content = renderMarriageLicenseDocument(false);
    const iframe = document.createElement('iframe');
    iframe.style.position = 'fixed';
    iframe.style.right = '0';
    iframe.style.bottom = '0';
    iframe.style.width = '0';
    iframe.style.height = '0';
    iframe.style.border = '0';
    document.body.appendChild(iframe);

    const html = `<!DOCTYPE html><html><head><title>Marriage License</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: Arial, Helvetica, sans-serif; background: #fff; color: #111; padding: 24px; font-size: 12px; line-height: 1.5; }
@page { size: A4; margin: 12mm; }
.lcr-official-form { border: 2px solid #333; border-radius: 10px; background: #fff; width: 100%; }
.lf-cert-header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #333; padding: 12px 16px; gap: 12px; }
.lf-cert-form-ref { font-size: 11px; line-height: 1.4; min-width: 125px; }
.lf-cert-title { flex: 1; text-align: center; line-height: 1.6; font-size: 12px; }
.lf-cert-title div:nth-child(2) { font-size: 18px; font-weight: 700; }
.lf-cert-date-box { min-width: 130px; text-align: right; font-size: 12px; }
.lf-cert-date-box .lf-fn { display: block; margin-bottom: 4px; }
.lf-val { display: inline-block; width: 100%; min-height: 18px; border-bottom: 1px solid #333; padding-bottom: 2px; }
.lf-cert-fields { padding: 12px 16px 4px; }
.lf-cert-row { display: flex; align-items: baseline; gap: 8px; padding: 4px 0; }
.lf-cert-label { min-width: 180px; }
.lf-cert-colon { width: 8px; }
.lf-cert-value { flex: 1; }
.marriage-license-banner { padding: 14px 16px 10px; text-align: center; }
.marriage-license-title { font-size: 24px; font-weight: 700; letter-spacing: 1px; margin-bottom: 8px; }
.marriage-license-banner p { font-size: 12px; }
.lf-table { width: calc(100% - 32px); margin: 0 16px 14px; border-collapse: collapse; table-layout: fixed; }
.lf-table th, .lf-table td { border: 1px solid #888; padding: 7px 8px; vertical-align: top; }
.lf-table th { background: #f4f4f4; font-weight: 700; }
.lf-cert-row-label { width: 170px; font-weight: 600; }
.marriage-license-certification { padding: 0 16px 14px; }
.marriage-license-certification p { margin-top: 8px; }
.marriage-license-footer { display: flex; justify-content: space-between; gap: 24px; padding: 18px 16px 16px; }
.marriage-license-signature-block { flex: 1; text-align: center; }
.marriage-license-signature-line .lf-val { min-height: 20px; }
.marriage-license-signature-label { margin-top: 8px; font-size: 11px; text-transform: uppercase; }
</style></head><body>${content}</body></html>`;

    const doc = iframe.contentWindow.document;
    doc.open();
    doc.write(html);
    doc.close();

    const runPrint = () => {
        if (iframe.dataset.printed === 'yes') return;
        iframe.dataset.printed = 'yes';
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
        setTimeout(() => iframe.remove(), 1000);
    };

    iframe.onload = runPrint;
    setTimeout(runPrint, 500);
}

function saveRecordChanges() {
    if (!_currentRecord.formData) _currentRecord.formData = {};

    // Collect all edited inputs from the modal
    document.querySelectorAll('#recordModalBody .lf-input').forEach(inp => {
        const key = inp.dataset.key;
        if (key === '_status') _currentRecord.status = inp.value;
        else _currentRecord.formData[key] = inp.value;
    });

    // Optimistically update local array & UI
    const idx = records.findIndex(r => r.id === _currentRecord.id);
    if (idx !== -1) records[idx] = { ..._currentRecord };
    displayRecords(records);
    _recordEditing = false;
    document.getElementById('recordEditBtn').textContent      = '✏️ EDIT';
    document.getElementById('recordEditBtn').style.background = '';
    document.getElementById('recordSaveBtn').style.display    = 'none';
    renderRecordBody(false);

    // Persist to DB → php/save_record.php
    fetch('php/save_record.php', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
            doc_id:   _currentRecord.doc_id,   // numeric DB id from get_records.php
            status:   _currentRecord.status,
            formData: _currentRecord.formData
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('Record saved successfully!', 'success');
        } else {
            showNotification('Save failed: ' + (data.message || 'Unknown error'), 'error');
        }
    })
    .catch(() => {
        showNotification('Could not reach server. Changes saved locally only.', 'error');
    });
}

// ── Print ─────────────────────────────────────────────────────
function printRecordModal() {
    if (_currentRecord && _currentRecord.type === 'marriage-license') {
        printMarriageLicenseCertificate();
        return;
    }

    const title   = document.getElementById('recordModalTitle').textContent;
    const content = document.getElementById('recordModalBody').innerHTML;
    const win = window.open('', '_blank');
    win.document.write(`<!DOCTYPE html><html><head><title>${title}</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: Arial, Helvetica, sans-serif; background: #fff; color: #111; padding: 32px 48px; font-size: 13px; line-height: 1.5; }
@page { margin: 15mm 18mm; }
.lf-input, .lf-select { display: none !important; }
.lf-val { display: inline-block; min-width: 120px; border-bottom: 1px solid #333; padding-bottom: 1px; font-size: 13px; word-break: break-word; vertical-align: bottom; }
.lf-section-label, .lf-table { display: none !important; }
.lf-fn { display: none !important; }
.lcr-official-form, .lcr-form-1a, .lcr-form-2a, .lcr-form-3a { border: none !important; background: transparent !important; width: 100%; padding: 0 !important; }
.lf-cert-header { display: flex !important; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #333 !important; padding-bottom: 14px !important; margin-bottom: 18px; }
.lf-cert-form-ref { font-size: 11px; color: #333; line-height: 1.5; min-width: 110px; }
.lf-cert-title { flex: 1; text-align: center; font-size: 13px; line-height: 1.8; padding: 0 16px; }
.lf-cert-title div:nth-child(2) { font-size: 20px; font-weight: bold; }
.lf-cert-title div:nth-child(3) .lf-val { border-bottom: 1px solid #333; min-width: 160px; display: inline-block; }
.lf-cert-date-box { font-size: 13px; text-align: right; min-width: 110px; display: flex !important; align-items: baseline; gap: 6px; justify-content: flex-end; }
.lf-cert-date-box .lf-val { min-width: 110px; }
.lf-cert-salutation { padding: 0 0 12px 0; font-size: 13px; line-height: 1.7; }
.lf-cert-salutation p { margin-top: 6px; text-indent: 2em; }
.lf-cert-fields { padding: 4px 0 14px 0; }
.lf-cert-row { display: flex !important; align-items: baseline; padding: 3px 0; border-bottom: none !important; }
.lf-cert-label { min-width: 200px; flex-shrink: 0; font-size: 13px; }
.lf-cert-colon { flex-shrink: 0; padding: 0 8px; }
.lf-cert-value { flex: 1; }
.lf-cert-value .lf-val { width: 100%; min-width: 0; border-bottom: 1px solid #333; display: block; }
.lf-cert-parties { width: 100%; border-collapse: collapse; margin: 10px 0 14px; table-layout: fixed; }
.lf-cert-parties th { background: none !important; color: #111; text-align: center; padding: 5px 10px; font-weight: bold; border: 1px solid #999; font-size: 13px; }
.lf-cert-parties td { border: 1px solid #999; padding: 5px 10px; font-size: 13px; vertical-align: middle; }
.lf-cert-row-label { font-size: 12px; color: #333; background: none !important; width: 160px; }
.lf-cert-parties .lf-val { display: block; width: 100%; border-bottom: 1px solid #555; min-width: 0; }
.lf-cert-issuance { padding: 14px 0; font-size: 13px; }
.lf-cert-issuance .lf-val { min-width: 220px; border-bottom: 1px solid #333; }
.lf-cert-bottom { display: flex !important; justify-content: space-between; align-items: flex-start; padding: 16px 0; border-top: 1px solid #ddd !important; gap: 40px; }
.lf-cert-verified { flex: 1; font-size: 13px; }
.lf-cert-sig-line { display: block; margin-top: 26px; border-bottom: 1px solid #333; min-width: 200px; max-width: 260px; padding-bottom: 2px; }
.lf-cert-sig-line .lf-val { border-bottom: none; display: inline-block; min-width: 180px; font-weight: 600; }
.lf-cert-payment { font-size: 13px; text-align: left; min-width: 180px; }
.lf-cert-pay-row { display: flex; align-items: baseline; gap: 0; padding: 3px 0; }
.lf-cert-pay-row span:first-child { min-width: 90px; }
.lf-cert-pay-row span:nth-child(2) { padding: 0 8px; }
.lf-cert-pay-row .lf-val { min-width: 90px; border-bottom: 1px solid #333; }
.lf-cert-note { padding: 18px 0 0 0; font-size: 12px; color: #555; font-style: italic; }
</style>
</head><body>${content}</body></html>`);
    win.document.close();
    setTimeout(() => { win.print(); win.close(); }, 500);
}

function closeRecordModal(e) {
    if (e && e.target !== document.getElementById('recordDetailModal')) return;
    document.getElementById('recordDetailModal').style.display = 'none';
    _currentRecord = null;
    _recordEditing = false;
}