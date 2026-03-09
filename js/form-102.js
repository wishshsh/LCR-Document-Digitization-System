// =============================================================
//  js/forms/form-102.js — Municipal Form No. 102
//                         Certificate of Live Birth
//  Requires: record-modal.js (_field, _statusField)
// =============================================================

function renderForm102(e) {
    const f = (k, p) => _field(k, p, e, false);
    const fw = (k, p) => _field(k, p, e, true);
    const hdr = '<div class="lcr-official-form">' +
        '<div class="lf-header-band">' +
            '<div class="lf-form-ref">Municipal Form No. 102<br><small>(Revised January 2007)</small></div>' +
            '<div class="lf-title-center">Republic of the Philippines<br>OFFICE OF THE CIVIL REGISTRAR GENERAL<br><strong>CERTIFICATE OF LIVE BIRTH</strong></div>' +
            '<div class="lf-reg-no">Registry No.<br>' + fw('registry_no','') + '</div>' +
        '</div>' +
        '<div class="lf-loc-row">' +
            '<div class="lf-loc-cell"><span class="lf-fn">Province</span>' + fw('province','') + '</div>' +
            '<div class="lf-loc-cell"><span class="lf-fn">City/Municipality</span>' + fw('city_municipality','') + '</div>' +
        '</div>';

    const child =
        '<div class="lf-section-label">CHILD</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">1. NAME — First</span>' + fw('child_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw('child_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw('child_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">2. SEX</span>' + f('sex','Male/Female') + '</td>' +
            '<td><span class="lf-fn">3. DATE OF BIRTH<br><small>Day / Month / Year</small></span>' +
                '<div class="lf-3col">' + f('dob_day','Day') + f('dob_month','Month') + f('dob_year','Year') + '</div></td>' +
            '<td><span class="lf-fn">6. WEIGHT AT BIRTH</span>' + f('weight','') + ' <small>grams</small></td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">4. PLACE OF BIRTH<br><small>Hospital/Clinic/Barangay</small></span>' + fw('pob_hospital','') + '</td>' +
            '<td><span class="lf-fn">City/Municipality</span>' + fw('pob_city','') + '</td>' +
            '<td><span class="lf-fn">Province</span>' + fw('pob_province','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">5a. TYPE OF BIRTH</span>' + f('type_of_birth','Single/Twin/etc.') + '</td>' +
            '<td><span class="lf-fn">5b. IF MULTIPLE BIRTH, CHILD WAS</span>' + f('birth_order','First/Second/etc.') + '</td>' +
            '<td><span class="lf-fn">5c. BIRTH ORDER</span>' + f('birth_order_total','e.g. First') + '</td>' +
        '</tr>' +
        '</table>';

    const mother =
        '<div class="lf-section-label">MOTHER</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">7. MAIDEN NAME — First</span>' + fw('mother_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw('mother_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw('mother_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">8. CITIZENSHIP</span>' + f('mother_citizenship','') + '</td>' +
            '<td><span class="lf-fn">9. RELIGION</span>' + f('mother_religion','') + '</td>' +
            '<td><span class="lf-fn">12. AGE AT TIME OF BIRTH</span>' + f('mother_age','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td colspan="2"><span class="lf-fn">13. RESIDENCE — House No., St., Barangay</span>' + fw('mother_address','') + '</td>' +
            '<td><span class="lf-fn">City/Municipality</span>' + fw('mother_city','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">Province</span>' + fw('mother_province','') + '</td>' +
            '<td><span class="lf-fn">10a. Total children born alive</span>' + f('mother_children_alive','') + '</td>' +
            '<td><span class="lf-fn">10b. Children still living</span>' + f('mother_children_living','') + '</td>' +
        '</tr>' +
        '</table>';

    const father =
        '<div class="lf-section-label">FATHER</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">14. NAME — First</span>' + fw('father_first','') + '</td>' +
            '<td><span class="lf-fn">Middle</span>' + fw('father_middle','') + '</td>' +
            '<td><span class="lf-fn">Last</span>' + fw('father_last','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">15. CITIZENSHIP</span>' + f('father_citizenship','') + '</td>' +
            '<td><span class="lf-fn">16. RELIGION</span>' + f('father_religion','') + '</td>' +
            '<td><span class="lf-fn">18. AGE AT TIME OF BIRTH</span>' + f('father_age','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td colspan="2"><span class="lf-fn">19. RESIDENCE — House No., St., Barangay</span>' + fw('father_address','') + '</td>' +
            '<td><span class="lf-fn">City/Municipality</span>' + fw('father_city','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">Province</span>' + fw('father_province','') + '</td>' +
            '<td><span class="lf-fn">17. OCCUPATION</span>' + f('father_occupation','') + '</td>' +
            '<td></td>' +
        '</tr>' +
        '</table>';

    const parents =
        '<div class="lf-section-label">MARRIAGE OF PARENTS</div>' +
        '<table class="lf-table">' +
        '<tr>' +
            '<td><span class="lf-fn">20a. DATE — Month</span>' + f('parents_marriage_month','') + '</td>' +
            '<td><span class="lf-fn">Day</span>' + f('parents_marriage_day','') + '</td>' +
            '<td><span class="lf-fn">Year</span>' + f('parents_marriage_year','') + '</td>' +
        '</tr>' +
        '<tr>' +
            '<td><span class="lf-fn">20b. PLACE — City/Municipality</span>' + fw('parents_marriage_city','') + '</td>' +
            '<td><span class="lf-fn">Province</span>' + fw('parents_marriage_province','') + '</td>' +
            '<td><span class="lf-fn">Country</span>' + fw('parents_marriage_country','') + '</td>' +
        '</tr>' +
        '</table>';

    const status =
        '<div class="lf-section-label">RECORD STATUS</div>' +
        '<table class="lf-table"><tr>' +
            '<td><span class="lf-fn">Status</span>' + _statusField(e) + '</td>' +
            '<td><span class="lf-fn">Date Submitted</span>' + f('date_submitted','YYYY-MM-DD') + '</td>' +
            '<td><span class="lf-fn">Prepared By</span>' + f('prepared_by','') + '</td>' +
        '</tr></table></div>';

    return hdr + child + mother + father + parents + status;
}

// ── FORM 103 — CERTIFICATE OF DEATH ──────────────────────────
