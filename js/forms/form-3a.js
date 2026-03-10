// ============================================================
//  FORM 3A — Certification of Marriage Facts
//  Used for both 'marriage-cert' and 'marriage-license' types
//  Depends on: record-modal.js (_field, _statusField, _currentRecord)
// ============================================================

function renderForm3A(e) {
    const f  = (k, p) => _field(k, p, e, false);
    const fw = (k, p) => _field(k, p, e, true);

    return `
    <div class="lcr-official-form lcr-form-3a">
        <div class="lf-cert-header">
            <div class="lf-cert-form-ref">LCR Form No. 3A<br><small>(Marriage available)</small></div>
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
            <p>&emsp;We certify that, among others, the following facts of marriage appear in our Registry of Marriages of this office:</p>
        </div>
        <div class="lf-cert-fields">
            <div class="lf-cert-row"><span class="lf-cert-label">Registry Number</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('registry_number', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date of Registration</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('date_of_registration', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Date of Marriage</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('date_of_marriage', '')}</span></div>
            <div class="lf-cert-row"><span class="lf-cert-label">Place of Marriage</span><span class="lf-cert-colon">:</span><span class="lf-cert-value">${fw('place_of_marriage', '')}</span></div>
        </div>
        <table class="lf-table lf-cert-parties">
            <thead>
                <tr><th></th><th>HUSBAND</th><th>WIFE</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td class="lf-cert-row-label">Name</td>
                    <td>${fw('husband_name', '')}</td>
                    <td>${fw('wife_name', '')}</td>
                </tr>
                <tr>
                    <td class="lf-cert-row-label">Age</td>
                    <td>${f('husband_age', '')}</td>
                    <td>${f('wife_age', '')}</td>
                </tr>
                <tr>
                    <td class="lf-cert-row-label">Nationality</td>
                    <td>${f('husband_nationality', '')}</td>
                    <td>${f('wife_nationality', '')}</td>
                </tr>
                <tr>
                    <td class="lf-cert-row-label">Name of Mother</td>
                    <td>${fw('husband_mother_name', '')}</td>
                    <td>${fw('wife_mother_name', '')}</td>
                </tr>
                <tr>
                    <td class="lf-cert-row-label">Nationality of Mother</td>
                    <td>${f('husband_mother_nationality', '')}</td>
                    <td>${f('wife_mother_nationality', '')}</td>
                </tr>
                <tr>
                    <td class="lf-cert-row-label">Name of Father</td>
                    <td>${fw('husband_father_name', '')}</td>
                    <td>${fw('wife_father_name', '')}</td>
                </tr>
                <tr>
                    <td class="lf-cert-row-label">Nationality of Father</td>
                    <td>${f('husband_father_nationality', '')}</td>
                    <td>${f('wife_father_nationality', '')}</td>
                </tr>
            </tbody>
        </table>
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
