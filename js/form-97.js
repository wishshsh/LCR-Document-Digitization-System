// =============================================================
//  js/forms/form-97.js — Municipal Form No. 97
//                        Certificate of Marriage
//  Requires: record-modal.js (_field, _statusField)
// =============================================================

function renderForm97(e) {
    const f = (k, p) => _field(k, p, e, false);
    const fw = (k, p) => _field(k, p, e, true);

    const party = (label, px) =>
        '<div class="lf-section-label">' + label + '</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">1. NAME — First</span>' + fw(px+'_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw(px+'_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw(px+'_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">2a. Date of Birth — Day/Month/Year</span>' +
                '<div class="lf-3col">' + f(px+'_dob_day','Day') + f(px+'_dob_month','Month') + f(px+'_dob_year','Year') + '</div></td>' +
            '<td><span class="lf-fn">2b. Age</span>' + f(px+'_age','') + '</td>' +
            '<td><span class="lf-fn">3. Place of Birth — City/Municipality</span>' + fw(px+'_pob_city','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">Province</span>' + fw(px+'_pob_province','') + '</td>' +
            '<td><span class="lf-fn">4a. Sex</span>' + f(px+'_sex','Male/Female') + '</td>' +
            '<td><span class="lf-fn">4b. Citizenship</span>' + f(px+'_citizenship','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td colspan="2"><span class="lf-fn">5. Residence</span>' + fw(px+'_residence','') + '</td>' +
            '<td><span class="lf-fn">6. Religion</span>' + f(px+'_religion','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">7. Civil Status</span>' + f(px+'_civil_status','') + '</td>' +
            '<td><span class="lf-fn">8. Name of Father — First</span>' + fw(px+'_father_first','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw(px+'_father_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">9. Father\'s Citizenship</span>' + f(px+'_father_citizenship','') + '</td>' +
            '<td><span class="lf-fn">10. Maiden Name of Mother — First</span>' + fw(px+'_mother_first','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw(px+'_mother_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">11. Mother\'s Citizenship</span>' + f(px+'_mother_citizenship','') + '</td>' +
            '<td colspan="2"><span class="lf-fn">12. Name of Person Who Gave Consent — First</span>' + fw(px+'_consent_first','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">13. Relationship</span>' + f(px+'_consent_relationship','') + '</td>' +
            '<td colspan="2"><span class="lf-fn">14. Residence</span>' + fw(px+'_consent_residence','') + '</td>' +
        '</tr>' +
        '</table>';

    const hdr =
        '<div class="lcr-official-form lf-plain">' +
        '<div class="lf-header-band">' +
            '<div class="lf-form-ref">Municipal Form No. 97<br><small>(Revised January 2007)</small></div>' +
            '<div class="lf-title-center">Republic of the Philippines<br>OFFICE OF THE CIVIL REGISTRAR GENERAL<br><strong>CERTIFICATE OF MARRIAGE</strong></div>' +
            '<div class="lf-reg-no">Registry No.<br>' + fw('registry_no','') + '</div>' +
        '</div>' +
        '<div class="lf-loc-row">' +
            '<div class="lf-loc-cell"><span class="lf-fn">Province</span>' + fw('province','') + '</div>' +
            '<div class="lf-loc-cell"><span class="lf-fn">City/Municipality</span>' + fw('city_municipality','') + '</div>' +
        '</div>';

    const details =
        '<div class="lf-section-label">MARRIAGE DETAILS</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">15. Place of Marriage — Office/Church/Mosque</span>' + fw('marriage_venue','') + '</td>' +
            '<td><span class="lf-fn">City/Municipality</span>' + fw('marriage_city','') + '</td>' +
            '<td><span class="lf-fn">Province</span>' + fw('marriage_province','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">16. Date of Marriage — Day/Month/Year</span>' +
                '<div class="lf-3col">' + f('marriage_day','Day') + f('marriage_month','Month') + f('marriage_year','Year') + '</div></td>' +
            '<td><span class="lf-fn">17. Time of Marriage</span>' + f('marriage_time','e.g. 10:00 AM') + '</td>' +
            '<td></td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">Marriage License No.</span>' + f('license_no','') + '</td>' +
            '<td><span class="lf-fn">Date Issued</span>' + f('license_date_issued','YYYY-MM-DD') + '</td>' +
            '<td><span class="lf-fn">Place Issued</span>' + f('license_place_issued','') + '</td>' +
        '</tr>' +
        '</table>';

    const status =
        '<div class="lf-section-label">RECORD STATUS</div>' +
        '<table class="lf-table"><tr>' +
            '<td><span class="lf-fn">Status</span>' + _statusField(e) + '</td>' +
            '<td><span class="lf-fn">Received By</span>' + f('received_by','') + '</td>' +
            '<td><span class="lf-fn">Date Received</span>' + f('date_received','YYYY-MM-DD') + '</td>' +
        '</tr></table></div>';

    return hdr + party('HUSBAND', 'husband') + party('WIFE', 'wife') + details + status;
}

// ── FORM 90 — APPLICATION FOR MARRIAGE LICENSE ────────────────
