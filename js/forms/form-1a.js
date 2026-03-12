// ============================================================
//  FORM 1A — Certification of Birth Facts
//  Depends on: record-modal.js (_field, _statusField, _currentRecord)
// ============================================================

function renderForm1A(e) {
    const f  = (k, p) => _field(k, p, e, false);
    const fw = (k, p) => _field(k, p, e, true);

    return `
    <div class="lcr-official-form lcr-form-1a">
        <div class="lf-cert-header">
            <div class="lf-cert-form-ref">LCR Form No. 1A<br><small>Certification of Birth</small></div>
            <div class="lf-cert-title">
                <div>Republic of the Philippines</div>
                <div>Office of the Municipal Registrar</div>
                <div>${_field('city', 'City/Municipality', true, true)}</div>
            </div>
            <div class="lf-cert-date-box">
                <span class="lf-fn">Date</span>
                ${fw('date', 'YYYY-MM-DD')}
            </div>
        </div>
        <div class="lf-cert-salutation">
            <strong>TO WHOM IT MAY CONCERN:</strong>
            <p>&emsp;We certify that, among others, the following facts of birth appear in our Registry of Births of this office:</p>
        </div>
        <div class="lf-cert-fields">
            <div class="lf-cert-row"><span class="lf-cert-label">Registry Number</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('registry_number', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date of Registration</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('date_of_registration', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Name of Child</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('child_name', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Sex</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${f('sex', 'Male / Female')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date of Birth</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('date_of_birth', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Place of Birth</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('place_of_birth', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Name of Mother</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('mother_name', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Nationality of Mother</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${f('mother_nationality', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Name of Father</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('father_name', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Nationality of Father</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${f('father_nationality', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date of Marriage of Parents</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('parents_marriage_date', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Place of Marriage of Parents</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('parents_marriage_place', '')}</span></div>
        </div>
        <div class="lf-cert-issuance">
            This certification is issued to ${fw('issued_to', 'Name of requesting party')} upon his/her request.
        </div>
        <div class="lf-cert-bottom">
            <div class="lf-cert-verified">
                <div class="lf-fn">Verified by:</div>
                <div class="lf-cert-sig-line">${fw('verified_by', '')}</div>
                <div class="lf-cert-sig-line">${fw('verified_position', '')}</div>
            </div>
            <div class="lf-cert-payment">
                <div class="lf-cert-pay-row"><span>Amount Paid</span><span>:</span>${f('amount_paid', '')}</div>
                <div class="lf-cert-pay-row"><span>OR Number</span><span>:</span>${f('or_number', '')}</div>
                <div class="lf-cert-pay-row"><span>Date Paid</span><span>:</span>${f('date_paid', '')}</div>
            </div>
        </div>
        <div class="lf-section-label">RECORD STATUS</div>
        <table class="lf-table"><tr>
            <td><span class="lf-fn">Status</span>${_statusField(e)}</td>
        </tr></table>
        <div class="lf-cert-note"><em>Note: A Mark, erasure or alteration of any entry invalidates this certification.</em></div>
    </div>`;
}