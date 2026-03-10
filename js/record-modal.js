// =============================================================
//  js/record-modal.js — viewRecord, renderRecordBody,
//                       toggleRecordEdit, saveRecordChanges,
//                       printRecordModal, closeRecordModal,
//                       _field helper, _statusField helper
//  Requires: globals.js, records.js, forms/form-*.js
// =============================================================

// ============================================================
//  RECORD DETAIL MODAL — Official LCR Form Renderers
// ============================================================
let _currentRecord = null;
let _recordEditing = false;

function _field(key, placeholder, editMode, wide) {
    const d = (_currentRecord.formData) || {};
    const v = (d[key] !== undefined) ? d[key] : '';
    if (editMode) {
        return '<input class="lf-input' + (wide ? ' lf-input-wide' : '') + '" data-key="' + key + '" value="' + v + '" placeholder="' + (placeholder || '') + '">';
    }
    return '<span class="lf-val">' + v + '</span>';
}

function _statusField(editMode) {
    const s = _currentRecord.status;
    if (!editMode) return '<span class="lf-status lf-status-' + s.toLowerCase() + '">' + s + '</span>';
    return '<select class="lf-input lf-select" data-key="_status">' +
        '<option' + (s==='Pending'   ?' selected':'') + '>Pending</option>' +
        '<option' + (s==='Approved'  ?' selected':'') + '>Approved</option>' +
        '<option' + (s==='Rejected'  ?' selected':'') + '>Rejected</option>' +
        '<option' + (s==='Processed' ?' selected':'') + '>Processed</option>' +
        '</select>';
}

function viewRecord(record) {
    if (!record.formData) record.formData = {};
    _currentRecord = record;
    _recordEditing = false;
    document.getElementById('recordModalTitle').textContent = formatType(record.type) + ' — ' + record.name;
    document.getElementById('recordEditBtn').textContent    = '✏️ EDIT';
    document.getElementById('recordEditBtn').style.background = '';
    document.getElementById('recordSaveBtn').style.display  = 'none';
    renderRecordBody(false);
    document.getElementById('recordDetailModal').style.display = 'flex';
}

function renderRecordBody(editMode) {
    const type = _currentRecord.type;
    let html = '';
    if      (type === 'birth')            html = renderForm102(editMode);
    else if (type === 'death')            html = renderForm103(editMode);
    else if (type === 'marriage-cert')    html = renderForm97(editMode);
    else if (type === 'marriage-license') html = renderForm90(editMode);
    document.getElementById('recordModalBody').innerHTML = html;
}

// ── FORM 102 — CERTIFICATE OF LIVE BIRTH ─────────────────────
// ── FORM 102 — CERTIFICATE OF LIVE BIRTH ─────────────────────
function toggleRecordEdit() {
    _recordEditing = !_recordEditing;
    const editBtn = document.getElementById('recordEditBtn');
    const saveBtn = document.getElementById('recordSaveBtn');
    editBtn.textContent      = _recordEditing ? '✖ CANCEL' : '✏️ EDIT';
    editBtn.style.background = _recordEditing ? '#aaa' : '';
    saveBtn.style.display    = _recordEditing ? 'inline-flex' : 'none';
    renderRecordBody(_recordEditing);
}

// ── SAVE CHANGES ──────────────────────────────────────────────
function saveRecordChanges() {
    if (!_currentRecord.formData) _currentRecord.formData = {};

    // Collect all edited values from the modal
    document.querySelectorAll('#recordModalBody .lf-input').forEach(inp => {
        const key = inp.dataset.key;
        if (key === '_status') _currentRecord.status = inp.value;
        else _currentRecord.formData[key] = inp.value;
    });

    // Update local records array immediately (optimistic UI)
    const idx = records.findIndex(r => r.id === _currentRecord.id);
    if (idx !== -1) records[idx] = { ..._currentRecord };
    displayRecords(records);

    _recordEditing = false;
    document.getElementById('recordEditBtn').textContent      = '✏️ EDIT';
    document.getElementById('recordEditBtn').style.background = '';
    document.getElementById('recordSaveBtn').style.display    = 'none';
    renderRecordBody(false);

    // Persist to database
    if (_currentRecord.doc_id) {
        fetch('php/save_record.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                doc_id:   _currentRecord.doc_id,
                status:   _currentRecord.status,
                formData: _currentRecord.formData
            })
        })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'success') {
                showNotification('Record saved to database!', 'success');
            } else {
                showNotification('Saved locally. DB error: ' + data.message, 'error');
            }
        })
        .catch(() => showNotification('Saved locally. Could not reach server.', 'error'));
    } else {
        showNotification('Record updated (local only — no doc_id).', 'success');
    }
}

// ── PRINT ─────────────────────────────────────────────────────
function printRecordModal() {
    const title   = document.getElementById('recordModalTitle').textContent;
    const content = document.getElementById('recordModalBody').innerHTML;
    const win = window.open('', '_blank');
    win.document.write('<!DOCTYPE html><html><head><title>' + title + '</title><style>' +
        '* { margin:0; padding:0; box-sizing:border-box; }' +
        'body { font-family: Arial, sans-serif; background:#fff; color:#111; padding:24px 32px; font-size:12px; }' +
        '.lf-input,.lf-select { display:none !important; }' +
        '.lf-val { display:inline-block; min-width:60px; border-bottom:1px solid #666; padding-bottom:1px; font-size:12px; }' +
        '.lf-status { padding:2px 8px; border-radius:3px; font-size:11px; font-weight:bold; display:inline-block; }' +
        '.lf-status-pending  { background:#fff3cd; color:#856404; }' +
        '.lf-status-approved { background:#d1e7dd; color:#0a3622; }' +
        '.lf-status-rejected { background:#f8d7da; color:#58151c; }' +
        '.lf-status-processed{ background:#cfe2ff; color:#084298; }' +
        '.lcr-official-form { border:2px solid #1a7a4a; width:100%; }' +
        '.lcr-official-form.lf-plain { border:2px solid #333; }' +
        '.lf-plain .lf-header-band { border-bottom:2px solid #333; }' +
        '.lf-plain .lf-reg-no { border:1.5px solid #333; }' +
        '.lf-plain .lf-loc-row { border-bottom:1.5px solid #333; }' +
        '.lf-plain .lf-loc-cell { border-right:1px solid #333; }' +
        '.lf-plain .lf-section-label { background:#2c3e50; }' +
        '.lf-plain .lf-table td,.lf-plain .lf-table th { border:1px solid #333; }' +
        '.lf-plain .lf-table th { background:#f0f0f0; color:#333; }' +
        '.lf-plain .lf-fn { color:#333; }' +
        '.lf-plain .lf-side-label { color:#333; }' +
        '.lf-header-band { display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2px solid #1a7a4a; padding:10px 12px; gap:10px; background:#fff; }' +
        '.lf-title-center { text-align:center; font-size:12px; flex:1; line-height:1.6; }' +
        '.lf-title-center strong { font-size:16px; display:block; margin-top:4px; letter-spacing:0.5px; }' +
        '.lf-form-ref { font-size:10px; color:#555; min-width:130px; }' +
        '.lf-reg-no { text-align:right; font-size:11px; border:1.5px solid #1a7a4a; padding:4px 10px; min-width:100px; }' +
        '.lf-loc-row { display:flex; border-bottom:1.5px solid #1a7a4a; }' +
        '.lf-loc-cell { flex:1; padding:5px 10px; font-size:12px; border-right:1px solid #1a7a4a; }' +
        '.lf-loc-cell:last-child { border-right:none; }' +
        '.lf-section-label { background:#1a7a4a; color:#fff; padding:4px 10px; font-size:11px; font-weight:bold; letter-spacing:0.5px; }' +
        '.lf-table { width:100%; border-collapse:collapse; }' +
        '.lf-table td,.lf-table th { border:1px solid #1a7a4a; padding:6px 8px; vertical-align:top; font-size:12px; }' +
        '.lf-table th { background:#e8f5f0; font-weight:bold; font-size:11px; text-align:center; color:#1a7a4a; }' +
        '.lf-fn { font-weight:bold; font-size:10px; color:#1a7a4a; display:block; margin-bottom:3px; }' +
        '.lf-sub { font-size:9px; color:#666; margin-right:2px; }' +
        '.lf-name-row { display:flex; flex-wrap:wrap; gap:6px; align-items:center; }' +
        '.lf-side-label { font-weight:bold; width:70px; font-size:11px; color:#1a7a4a; }' +
        '.lf-3col { display:flex; gap:8px; flex-wrap:nowrap; align-items:center; margin-top:3px; }' +
        '.lf-3col .lf-val { flex:1; min-width:0; }' +
        '.lf-table td { overflow:hidden; word-break:break-word; }' +
        '.lf-val { max-width:100%; word-break:break-word; }' +
        '</style></head><body>' + content + '</body></html>');
    win.document.close();
    setTimeout(() => { win.print(); win.close(); }, 500);
}

// ── CLOSE MODAL ───────────────────────────────────────────────
function closeRecordModal(e) {
    if (e && e.target !== document.getElementById('recordDetailModal')) return;
    document.getElementById('recordDetailModal').style.display = 'none';
    _currentRecord = null;
    _recordEditing = false;
}
