// =============================================================
//  js/templates.js — toggleTemplateEdit, saveTemplateChanges,
//                    printTemplate (cert / marriage views)
//  Requires: globals.js, navigation.js
// =============================================================

// ============================================================
//  TEMPLATE EDIT / SAVE CHANGES / PRINT
// ============================================================
const _tplEditing = { cert: false, marriage: false };

function toggleTemplateEdit(ctx) {
    _tplEditing[ctx] = !_tplEditing[ctx];
    const box     = document.getElementById(ctx + 'TemplateBox');
    const editBtn = document.getElementById(ctx + 'EditBtn');
    const saveBtn = document.getElementById(ctx + 'SaveChangesBtn');

    if (_tplEditing[ctx]) {
        box.contentEditable = 'true';
        box.style.outline   = '2px dashed #1ec77c';
        box.style.minHeight = '80px';
        editBtn.textContent      = '✖ CANCEL';
        editBtn.style.background = '#aaa';
        saveBtn.style.display    = 'inline-flex';
    } else {
        box.contentEditable      = 'false';
        box.style.outline        = '';
        editBtn.textContent      = '✏️ EDIT';
        editBtn.style.background = '';
        saveBtn.style.display    = 'none';
    }
}

function saveTemplateChanges(ctx) {
    _tplEditing[ctx] = false;
    const box     = document.getElementById(ctx + 'TemplateBox');
    const editBtn = document.getElementById(ctx + 'EditBtn');
    const saveBtn = document.getElementById(ctx + 'SaveChangesBtn');
    box.contentEditable      = 'false';
    box.style.outline        = '';
    editBtn.textContent      = '✏️ EDIT';
    editBtn.style.background = '';
    saveBtn.style.display    = 'none';
    showNotification('Changes saved!', 'success');
}

function printTemplate(boxId) {
    const box = document.getElementById(boxId);
    if (!box) return;
    const win = window.open('', '_blank');
    win.document.write(`<!DOCTYPE html><html><head><title>Civil Registry Form</title>
        <style>
            body { font-family: 'Times New Roman', serif; margin: 60px; text-align: center; }
            .tbox { border: 1px solid #999; padding: 60px 40px; display: inline-block; font-size: 18px; min-width: 320px; }
        </style></head><body>
        <div class="tbox">${box.innerHTML}</div>
        </body></html>`);
    win.document.close();
    setTimeout(() => { win.print(); win.close(); }, 300);
}

// ============================================================
