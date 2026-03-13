// ============================================================
//  TEMPLATES — Upload-preview form edit / save / print
//  Depends on: globals.js, navigation.js
// ============================================================

// _tplEditing is declared in globals.js


function toggleTemplateEdit(ctx) {
    _tplEditing[ctx] = !_tplEditing[ctx];
    const box     = document.getElementById(ctx + 'TemplateBox');
    const editBtn = document.getElementById(ctx + 'EditBtn');
    const saveBtn = document.getElementById(ctx + 'SaveChangesBtn');

    if (_tplEditing[ctx]) {
        box.contentEditable      = 'true';
        box.style.outline        = '2px dashed #1ec77c';
        box.style.minHeight      = '80px';
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
    // Determine which form is active
    const isMarriage = boxId === 'marriageTemplateBox';
    const prefix     = isMarriage ? 'marriage' : 'cert';

    // Find the active form variant
    const box = document.getElementById(boxId);
    if (!box) return;
    const activeForm = box.querySelector('.lcr-form-variant.active-form');
    if (!activeForm) return;

    // Detect form type from active form's ID
    const formId = activeForm.id; // form1A, form2A, form3A
    const is1A = formId === 'form1A';
    const is2A = formId === 'form2A';
    const is3A = formId === 'form3A';

    // Helper to get span value by ID
    const v = (id) => {
        const el = document.getElementById(id);
        return el ? (el.textContent.trim() || '') : '';
    };

    // Determine prefix (f1a, f2a, f3a)
    const fp = is1A ? 'f1a' : is2A ? 'f2a' : 'f3a';

    // Build field rows
    function row(label, val) {
        return `<div class="pr"><span class="pl">${label}</span><span class="pc">:</span><span class="pv">${val}</span></div>`;
    }

    // Header
    const formNo   = is1A ? '1A' : is2A ? '2A' : '3A';
    const formName = is1A ? '(Birth available)' : is2A ? '(Death available)' : '(Marriage available)';
    const salutation = is1A
        ? 'We certify that, among others, the following facts of birth appear in our Registry of Births of this office:'
        : is2A
        ? 'We certify that, among others, the following facts of death appear in our Registry of Deaths of this office:'
        : 'We certify that, among others, the following facts of marriage appear in our Registry of Marriages of this office:';

    // Fields section
    let fieldsHtml = '';
    if (is1A) {
        fieldsHtml = `
            ${row('Registry Number',              v(fp+'_registry'))}
            ${row('Date of Registration',         v(fp+'_date_reg'))}
            ${row('Name of Child',                v(fp+'_child_name'))}
            ${row('Sex',                          v(fp+'_sex'))}
            ${row('Date of Birth',                v(fp+'_dob'))}
            ${row('Place of Birth',               v(fp+'_pob'))}
            ${row('Name of Mother',               v(fp+'_mother_name'))}
            ${row('Nationality of Mother',        v(fp+'_mother_nat'))}
            ${row('Name of Father',               v(fp+'_father_name'))}
            ${row('Nationality of Father',        v(fp+'_father_nat'))}
            ${row('Date of Marriage of Parents',  v(fp+'_marriage_date'))}
            ${row('Place of Marriage of Parents', v(fp+'_marriage_place'))}`;
    } else if (is2A) {
        fieldsHtml = `
            ${row('Registry Number',   v(fp+'_registry'))}
            ${row('Date of Registration', v(fp+'_date_reg'))}
            ${row('Name of Deceased',  v(fp+'_deceased_name'))}
            ${row('Sex',               v(fp+'_sex'))}
            ${row('Age',               v(fp+'_age'))}
            ${row('Civil Status',      v(fp+'_civil_status'))}
            ${row('Nationality',       v(fp+'_nationality'))}
            ${row('Date of Death',     v(fp+'_dod'))}
            ${row('Place of Death',    v(fp+'_pod'))}
            ${row('Cause of Death',    v(fp+'_cause'))}`;
    } else {
        // Form 3A — marriage table
        fieldsHtml = `
            ${row('Registry Number',     v(fp+'_registry'))}
            ${row('Date of Registration',v(fp+'_date_reg'))}
            ${row('Date of Marriage',    v(fp+'_dom'))}
            ${row('Place of Marriage',   v(fp+'_pom'))}
            <table class="ptable">
                <thead><tr><th></th><th>HUSBAND</th><th>WIFE</th></tr></thead>
                <tbody>
                    <tr><td>Name</td><td>${v(fp+'_husband_name')}</td><td>${v(fp+'_wife_name')}</td></tr>
                    <tr><td>Age</td><td>${v(fp+'_husband_age')}</td><td>${v(fp+'_wife_age')}</td></tr>
                    <tr><td>Nationality</td><td>${v(fp+'_husband_nat')}</td><td>${v(fp+'_wife_nat')}</td></tr>
                    <tr><td>Name of Mother</td><td>${v(fp+'_husband_mother')}</td><td>${v(fp+'_wife_mother')}</td></tr>
                    <tr><td>Nationality of Mother</td><td>${v(fp+'_husband_mother_nat')}</td><td>${v(fp+'_wife_mother_nat')}</td></tr>
                    <tr><td>Name of Father</td><td>${v(fp+'_husband_father')}</td><td>${v(fp+'_wife_father')}</td></tr>
                    <tr><td>Nationality of Father</td><td>${v(fp+'_husband_father_nat')}</td><td>${v(fp+'_wife_father_nat')}</td></tr>
                </tbody>
            </table>`;
    }

    const html = `<!DOCTYPE html><html><head>
<title>LCR Form No. ${formNo}</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 13px; color: #111; background:#fff; padding: 36px 52px; line-height:1.6; }
@page { size: A4; margin: 14mm 16mm; }

/* Header */
.ph { display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2px solid #333; padding-bottom:12px; margin-bottom:16px; }
.ph-ref { font-size:11px; color:#444; line-height:1.6; min-width:110px; }
.ph-title { flex:1; text-align:center; padding:0 16px; }
.ph-office { font-size:17px; font-weight:bold; }
.ph-city { font-size:13px; font-weight:600; min-height:18px; border-bottom:1px solid #333; display:inline-block; min-width:160px; }
.ph-date { font-size:13px; text-align:right; min-width:110px; display:flex; align-items:baseline; gap:6px; justify-content:flex-end; }
.pv-inline { display:inline-block; border-bottom:1px solid #333; min-width:100px; font-weight:600; }

/* Salutation */
.psalutation { margin-bottom:14px; font-size:13px; }
.psalutation p { text-indent:2em; margin-top:5px; }

/* Field rows */
.pfields { margin-bottom:16px; }
.pr { display:flex; align-items:baseline; padding:4px 0; border-bottom:1px dotted #ccc; }
.pl { min-width:230px; flex-shrink:0; color:#444; }
.pc { padding:0 10px; color:#666; flex-shrink:0; }
.pv { flex:1; font-weight:600; border-bottom:1px solid #333; min-width:80px; display:block; }

/* Marriage table */
.ptable { width:100%; border-collapse:collapse; margin:12px 0 16px; }
.ptable th { background:#2c3e50; color:white; padding:7px 12px; text-align:center; }
.ptable td { border:1px solid #bbb; padding:5px 12px; }
.ptable td:first-child { background:#f5f5f5; color:#444; width:170px; font-size:12px; }

/* Issuance */
.pissue { padding:14px 0; font-size:13px; border-top:1px solid #ddd; }
.pv-issue { display:inline-block; border-bottom:1px solid #333; min-width:220px; font-weight:600; }

/* Bottom */
.pbottom { display:flex; justify-content:space-between; align-items:flex-start; padding:20px 0 16px; border-top:1px solid #ddd; margin-top:8px; gap:40px; }
.pbottom-left { flex:1; }
.psig-lbl { font-size:12px; color:#555; margin-bottom:28px; display:block; }
.psig-line { display:inline-block; border-bottom:1.5px solid #333; min-width:240px; padding-bottom:2px; font-size:13px; font-weight:600; margin-bottom:6px; }
.pbottom-right { font-size:13px; min-width:200px; }
.ppay { display:flex; gap:8px; padding:3px 0; }
.ppay span:first-child { min-width:100px; color:#555; }
.ppay .pv-inline { min-width:90px; }

/* Note */
.pnote { margin-top:20px; font-size:11px; color:#777; font-style:italic; border-top:1px solid #eee; padding-top:10px; }
</style>
</head><body>

<div class="ph">
    <div class="ph-ref">LCR Form No. ${formNo}<br><small>${formName}</small></div>
    <div class="ph-title">
        <div>Republic of the Philippines</div>
        <div class="ph-office">Office of the Municipal Registrar</div>
        <div><span class="ph-city">${v(fp+'_city')}</span></div>
    </div>
    <div class="ph-date"><span>Date:</span><span class="pv-inline">${v(fp+'_date')}</span></div>
</div>

<div class="psalutation">
    <strong>TO WHOM IT MAY CONCERN:</strong>
    <p>${salutation}</p>
</div>

<div class="pfields">${fieldsHtml}</div>

<div class="pissue">
    This certification is issued to <span class="pv-issue">${v(fp+'_issued_to')}</span> upon his/her request.
</div>

<div class="pbottom">
    <div class="pbottom-left">
        <span class="psig-lbl">Verified by:</span>
        <div class="psig-line">${v(fp+'_verified_by')}</div>
        <div class="psig-line" style="font-size:12px;font-weight:normal;">${v(fp+'_verified_pos')}</div>
    </div>
    <div class="pbottom-right">
        <div class="ppay"><span>Amount Paid</span><span>:</span><span class="pv-inline">${v(fp+'_amount')}</span></div>
        <div class="ppay"><span>OR Number</span><span>:</span><span class="pv-inline">${v(fp+'_or_number')}</span></div>
        <div class="ppay"><span>Date Paid</span><span>:</span><span class="pv-inline">${v(fp+'_date_paid')}</span></div>
    </div>
</div>

<div class="pnote">Note: A Mark, erasure or alteration of any entry invalidates this certification.</div>

</body></html>`;

    const win = window.open('', '_blank');
    win.document.write(html);
    win.document.close();
    setTimeout(() => { win.print(); win.close(); }, 400);
}