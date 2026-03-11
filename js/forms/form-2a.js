// ============================================================
//  FORM 2A — Certification of Death Facts
//  Depends on: record-modal.js (_field, _statusField, _currentRecord)
// ============================================================

function renderForm2A(e) {
    const f  = (k, p) => _field(k, p, e, false);
    const fw = (k, p) => _field(k, p, e, true);

    return `
    <div class="lcr-official-form lcr-form-2a">
        <div class="lf-cert-header">
            <div class="lf-cert-form-ref">LCR Form No. 2A<br><small>(Death available)</small></div>
            <div class="lf-cert-title">
                <div>Republic of the Philippines</div>
                <div>Office of the City Registrar</div>
                <div>${fw('city', 'City/Municipality')}</div>
            </div>
            <div class="lf-cert-date-box">
                <span class="lf-fn">Date</span>
                ${fw('date', 'YYYY-MM-DD')}
            </div>
        </div>
        <div class="lf-cert-salutation">
            <strong>TO WHOM IT MAY CONCERN:</strong>
            <p>&emsp;We certify that, among others, the following facts of death appear in our Registry of Deaths of this office:</p>
        </div>
        <div class="lf-cert-fields">
            <div class="lf-cert-row"><span class="lf-cert-label">Registry Number</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('registry_number', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date of Registration</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('date_of_registration', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Name of Deceased</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('deceased_name', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Sex</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${f('sex', 'Male / Female')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Age</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${f('age', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Civil Status</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${f('civil_status', 'Single / Married / etc.')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Nationality</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${f('nationality', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date of Death</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('date_of_death', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Place of Death</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('place_of_death', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Cause of Death</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('cause_of_death', '')}</span></div>
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
