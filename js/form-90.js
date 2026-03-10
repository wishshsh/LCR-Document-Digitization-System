// =============================================================
//  js/forms/form-90.js — Municipal Form No. 90
//                        Application for Marriage License
//  Requires: record-modal.js (_field, _statusField)
// =============================================================

function renderForm90(e) {
    const f = (k, p) => _field(k, p, e, false);
    const fw = (k, p) => _field(k, p, e, true);

    const applicant = (label, px) =>
        '<div class="lf-section-label">' + label + '</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">1. Name — First</span>' + fw(px+'_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw(px+'_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw(px+'_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">2. Date of Birth — Day/Month/Year</span>' +
                '<div class="lf-3col">' + f(px+'_dob_day','Day') + f(px+'_dob_month','Month') + f(px+'_dob_year','Year') + '</div></td>' +
            '<td><span class="lf-fn">Age</span>' + f(px+'_age','') + '</td>' +
            '<td><span class="lf-fn">3. Place of Birth — City/Municipality</span>' + fw(px+'_pob_city','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">Province</span>' + fw(px+'_pob_province','') + '</td>' +
            '<td><span class="lf-fn">4. Sex</span>' + f(px+'_sex','Male/Female') + '</td>' +
            '<td><span class="lf-fn">Citizenship</span>' + f(px+'_citizenship','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td colspan="2"><span class="lf-fn">5. Residence</span>' + fw(px+'_residence','') + '</td>' +
            '<td><span class="lf-fn">6. Religion</span>' + f(px+'_religion','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">7. Civil Status</span>' + f(px+'_civil_status','') + '</td>' +
            '<td><span class="lf-fn">8. If Previously Married — How Dissolved</span>' + f(px+'_prev_marriage','') + '</td>' +
            '<td><span class="lf-fn">11. Degree of Relationship</span>' + f(px+'_relationship_degree','None') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">12. Name of Father — First</span>' + fw(px+'_father_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw(px+'_father_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw(px+'_father_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">13. Father\'s Citizenship</span>' + f(px+'_father_citizenship','') + '</td>' +
            '<td colspan="2"><span class="lf-fn">14. Father\'s Residence</span>' + fw(px+'_father_residence','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">15. Maiden Name of Mother — First</span>' + fw(px+'_mother_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw(px+'_mother_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw(px+'_mother_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">16. Mother\'s Citizenship</span>' + f(px+'_mother_citizenship','') + '</td>' +
            '<td colspan="2"><span class="lf-fn">17. Mother\'s Residence</span>' + fw(px+'_mother_residence','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td colspan="3"><span class="lf-fn">18. Person Who Gave Consent/Advice</span>' + fw(px+'_consent_person','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">19. Relationship</span>' + f(px+'_consent_relationship','') + '</td>' +
            '<td><span class="lf-fn">20. Citizenship</span>' + f(px+'_consent_citizenship','') + '</td>' +
            '<td><span class="lf-fn">21. Residence</span>' + fw(px+'_consent_residence','') + '</td>' +
        '</tr>' +
        '</table>';

    const hdr =
        '<div class="lcr-official-form lf-plain">' +
        '<div class="lf-header-band">' +
            '<div class="lf-form-ref">Municipal Form 90 (Form No. 2)<br><small>(Revised January 2007)</small></div>' +
            '<div class="lf-title-center">Republic of the Philippines<br>OFFICE OF THE CIVIL REGISTRAR GENERAL<br><strong>APPLICATION FOR MARRIAGE LICENSE</strong></div>' +
            '<div class="lf-reg-no">Registry No.<br>' + fw('registry_no','') + '</div>' +
        '</div>' +
        '<div class="lf-loc-row">' +
            '<div class="lf-loc-cell"><span class="lf-fn">Province</span>' + fw('province','') + '</div>' +
            '<div class="lf-loc-cell"><span class="lf-fn">City/Municipality</span>' + fw('city_municipality','') + '</div>' +
        '</div>' +
        '<table class="lf-table"><tr>' +
            '<td><span class="lf-fn">Received by</span>' + fw('received_by','') + '</td>' +
            '<td><span class="lf-fn">Marriage License No.</span>' + f('license_no','') + '</td>' +
        '</tr><tr>' +
            '<td><span class="lf-fn">Date of Receipt</span>' + f('date_receipt','YYYY-MM-DD') + '</td>' +
            '<td><span class="lf-fn">Date of Issuance of Marriage License</span>' + f('date_issuance','YYYY-MM-DD') + '</td>' +
        '</tr></table>';

    const status =
        '<div class="lf-section-label">RECORD STATUS</div>' +
        '<table class="lf-table"><tr>' +
            '<td><span class="lf-fn">Status</span>' + _statusField(e) + '</td>' +
            '<td><span class="lf-fn">Processed By</span>' + f('processed_by','') + '</td>' +
            '<td><span class="lf-fn">Date Processed</span>' + f('date_processed','YYYY-MM-DD') + '</td>' +
        '</tr></table></div>';

    return hdr + applicant('GROOM', 'groom') + applicant('BRIDE', 'bride') + status;
}

