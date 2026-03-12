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
    else if (type === 'marriage-license') html = renderForm3A(editMode);
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