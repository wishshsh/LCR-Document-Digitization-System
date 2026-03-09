// =============================================================
//  js/forms/form-103.js — Municipal Form No. 103
//                         Certificate of Death
//  Requires: record-modal.js (_field, _statusField)
// =============================================================

function renderForm103(e) {
    const f = (k, p) => _field(k, p, e, false);
    const fw = (k, p) => _field(k, p, e, true);
    const hdr =
        '<div class="lcr-official-form lf-plain">' +
        '<div class="lf-header-band">' +
            '<div class="lf-form-ref">Municipal Form No. 103<br><small>(Revised January 1993)</small></div>' +
            '<div class="lf-title-center">Republic of the Philippines<br>OFFICE OF THE CIVIL REGISTRAR GENERAL<br><strong>CERTIFICATE OF DEATH</strong></div>' +
            '<div class="lf-reg-no">Registry No.<br>' + fw('registry_no','') + '</div>' +
        '</div>' +
        '<div class="lf-loc-row">' +
            '<div class="lf-loc-cell"><span class="lf-fn">Province</span>' + fw('province','') + '</div>' +
            '<div class="lf-loc-cell"><span class="lf-fn">City/Municipality</span>' + fw('city_municipality','') + '</div>' +
        '</div>';

    const main =
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">1. NAME — First</span>' + fw('deceased_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw('deceased_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw('deceased_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">2. SEX</span>' + f('sex','Male/Female') + '</td>' +
            '<td><span class="lf-fn">3. RELIGION</span>' + f('religion','') + '</td>' +
            '<td><span class="lf-fn">4. AGE — Years / Months / Days</span>' +
                '<div class="lf-3col">' + f('age_years','Yrs') + f('age_months','Mo') + f('age_days','Days') + '</div></td>' +
        '</tr>' +
        '<tr>' +
            '<td colspan="2"><span class="lf-fn">5. PLACE OF DEATH — Hospital/Barangay</span>' + fw('pod_hospital','') + '</td>' +
            '<td><span class="lf-fn">City/Municipality</span>' + fw('pod_city','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">Province</span>' + fw('pod_province','') + '</td>' +
            '<td><span class="lf-fn">6. DATE OF DEATH — Day / Month / Year</span>' +
                '<div class="lf-3col">' + f('dod_day','Day') + f('dod_month','Month') + f('dod_year','Year') + '</div></td>' +
            '<td><span class="lf-fn">7. CITIZENSHIP</span>' + f('citizenship','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td colspan="2"><span class="lf-fn">8. RESIDENCE — House No., St., Barangay</span>' + fw('residence_address','') + '</td>' +
            '<td><span class="lf-fn">City/Municipality</span>' + fw('residence_city','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">Province</span>' + fw('residence_province','') + '</td>' +
            '<td><span class="lf-fn">9. CIVIL STATUS</span>' + f('civil_status','Single/Married/etc.') + '</td>' +
            '<td><span class="lf-fn">10. OCCUPATION</span>' + f('occupation','') + '</td>' +
        '</tr>' +
        '</table>';

    const causes =
        '<div class="lf-section-label">MEDICAL CERTIFICATE — CAUSES OF DEATH</div>' +
        '<table class="lf-table">' +
        '<tr><td><span class="lf-fn">17a. Immediate Cause</span>' + fw('cause_immediate','') + '</td></tr>' +
        '<tr><td><span class="lf-fn">17b. Antecedent Cause</span>' + fw('cause_antecedent','') + '</td></tr>' +
        '<tr><td><span class="lf-fn">17c. Underlying Cause</span>' + fw('cause_underlying','') + '</td></tr>' +
        '<tr><td><span class="lf-fn">17d. Other Significant Conditions Contributing to Death</span>' + fw('cause_other','') + '</td></tr>' +
        '</table>';

    const disposal =
        '<div class="lf-section-label">DISPOSAL</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">21. CORPSE DISPOSAL</span>' + f('corpse_disposal','Burial/Cremation') + '</td>' +
            '<td><span class="lf-fn">22. BURIAL/CREMATION PERMIT No.</span>' + f('burial_permit_no','') + '</td>' +
            '<td><span class="lf-fn">Date Issued</span>' + f('burial_permit_date','YYYY-MM-DD') + '</td>' +
            '<td><span class="lf-fn">23. AUTOPSY</span>' + f('autopsy','Yes/No') + '</td>' +
        '</tr>' +
        '<tr><td colspan="4"><span class="lf-fn">24. NAME AND ADDRESS OF CEMETERY/CREMATORY</span>' + fw('cemetery_address','') + '</td></tr>' +
        '</table>';

    const informant =
        '<div class="lf-section-label">INFORMANT</div>' +
        '<table class="lf-table"><tr>' +
            '<td><span class="lf-fn">Name in Print</span>' + fw('informant_name','') + '</td>' +
            '<td><span class="lf-fn">Relationship to Deceased</span>' + f('informant_relationship','') + '</td>' +
            '<td><span class="lf-fn">Address</span>' + fw('informant_address','') + '</td>' +
            '<td><span class="lf-fn">Date</span>' + f('informant_date','YYYY-MM-DD') + '</td>' +
        '</tr></table>';

    const status =
        '<div class="lf-section-label">RECORD STATUS</div>' +
        '<table class="lf-table"><tr>' +
            '<td><span class="lf-fn">Status</span>' + _statusField(e) + '</td>' +
            '<td><span class="lf-fn">Prepared By</span>' + f('prepared_by','') + '</td>' +
            '<td><span class="lf-fn">Date Received</span>' + f('date_received','YYYY-MM-DD') + '</td>' +
        '</tr></table></div>';

    return hdr + main + causes + disposal + informant + status;
}

// ── FORM 97 — CERTIFICATE OF MARRIAGE ────────────────────────
