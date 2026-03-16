import 'dart:convert';
import 'dart:io';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:url_launcher/url_launcher.dart';

class PrintService {
  /// Generates the certificate HTML, saves it to a temp file,
  /// and opens it in the default browser. The page has a Print button
  /// that triggers window.print() so the user gets the print dialog.
  static Future<void> printRecord(Map<String, dynamic> record) async {
    final type = record['type'] ?? '';
    final d    = Map<String, dynamic>.from(record['formData'] ?? {});

    String v(String key) {
      final val = d[key];
      return (val == null || val.toString().trim().isEmpty) ? '' : val.toString();
    }

    final is1A = type == 'birth';
    final is2A = type == 'death';
    final formNo   = is1A ? '1A' : is2A ? '2A' : type == 'marriage-cert' ? '3A' : '90';
    final formName = is1A ? '(Birth Certificate)'
                   : is2A ? '(Death Certificate)'
                   : type == 'marriage-cert' ? '(Marriage Certificate)'
                   : '(Marriage License)';
    final salutation = is1A
        ? 'We certify that, among others, the following facts of birth appear in our Registry of Births of this office:'
        : is2A
        ? 'We certify that, among others, the following facts of death appear in our Registry of Deaths of this office:'
        : 'We certify that, among others, the following facts of marriage appear in our Registry of Marriages of this office:';

    String row(String label, String val) =>
        '<div class="pr"><span class="pl">$label</span><span class="pc">:</span><span class="pv">$val</span></div>';

    // ── Build fields section ────────────────────────────────
    String fieldsHtml;
    if (is1A) {
      fieldsHtml = '''
        ${row('Registry Number',              v('registry_number'))}
        ${row('Date of Registration',         v('date_of_registration'))}
        ${row('Name of Child',                v('child_name'))}
        ${row('Sex',                          v('sex'))}
        ${row('Date of Birth',                v('date_of_birth'))}
        ${row('Place of Birth',               v('place_of_birth'))}
        ${row('Name of Mother',               v('mother_name'))}
        ${row('Nationality of Mother',        v('mother_nationality'))}
        ${row('Name of Father',               v('father_name'))}
        ${row('Nationality of Father',        v('father_nationality'))}
        ${row('Date of Marriage of Parents',  v('parents_marriage_date'))}
        ${row('Place of Marriage of Parents', v('parents_marriage_place'))}
      ''';
    } else if (is2A) {
      fieldsHtml = '''
        ${row('Registry Number',    v('registry_number'))}
        ${row('Date of Registration', v('date_of_registration'))}
        ${row('Name of Deceased',   v('deceased_name'))}
        ${row('Sex',                v('sex'))}
        ${row('Age',                v('age'))}
        ${row('Civil Status',       v('civil_status'))}
        ${row('Nationality',        v('nationality'))}
        ${row('Date of Death',      v('date_of_death'))}
        ${row('Place of Death',     v('place_of_death'))}
        ${row('Cause of Death',     v('cause_of_death'))}
      ''';
    } else if (type == 'marriage-cert') {
      // Form 3A — fields pre-assembled as husband_name / wife_name by get_records.php
      fieldsHtml = '''
        ${row('Registry Number',      v('registry_number'))}
        ${row('Date of Registration', v('date_of_registration'))}
        ${row('Date of Marriage',     v('date_of_marriage'))}
        ${row('Place of Marriage',    v('place_of_marriage'))}
        <table class="ptable">
          <thead><tr><th></th><th>HUSBAND</th><th>WIFE</th></tr></thead>
          <tbody>
            <tr><td>Name</td><td>${v('husband_name')}</td><td>${v('wife_name')}</td></tr>
            <tr><td>Age</td><td>${v('husband_age')}</td><td>${v('wife_age')}</td></tr>
            <tr><td>Nationality</td><td>${v('husband_nationality')}</td><td>${v('wife_nationality')}</td></tr>
            <tr><td>Name of Mother</td><td>${v('husband_mother_name')}</td><td>${v('wife_mother_name')}</td></tr>
            <tr><td>Name of Father</td><td>${v('husband_father_name')}</td><td>${v('wife_father_name')}</td></tr>
          </tbody>
        </table>
      ''';
    } else {
      // Form 90 — Marriage License
      // Fields stored as groom_first/groom_last/bride_first/bride_last etc.
      final groomName = [v('groom_first'), v('groom_middle'), v('groom_last')]
          .where((s) => s.isNotEmpty).join(' ');
      final brideName = [v('bride_first'), v('bride_middle'), v('bride_last')]
          .where((s) => s.isNotEmpty).join(' ');
      final groomMother = [v('groom_mother_first'), v('groom_mother_last')]
          .where((s) => s.isNotEmpty).join(' ');
      final groomFather = [v('groom_father_first'), v('groom_father_last')]
          .where((s) => s.isNotEmpty).join(' ');
      final brideMother = [v('bride_mother_first'), v('bride_mother_last')]
          .where((s) => s.isNotEmpty).join(' ');
      final brideFather = [v('bride_father_first'), v('bride_father_last')]
          .where((s) => s.isNotEmpty).join(' ');
      final dateOfMarriage = [v('marriage_month'), v('marriage_day'), v('marriage_year')]
          .where((s) => s.isNotEmpty).join(' ');
      final placeOfMarriage = [v('marriage_venue'), v('marriage_city'), v('marriage_province')]
          .where((s) => s.isNotEmpty).join(', ');

      fieldsHtml = '''
        ${row('Registry Number',      v('registry_no'))}
        ${row('License Number',       v('license_no'))}
        ${row('Date of Registration', v('date_of_registration'))}
        ${row('Date of Marriage',     dateOfMarriage)}
        ${row('Place of Marriage',    placeOfMarriage)}
        <table class="ptable">
          <thead><tr><th></th><th>HUSBAND / GROOM</th><th>WIFE / BRIDE</th></tr></thead>
          <tbody>
            <tr><td>Name</td><td>$groomName</td><td>$brideName</td></tr>
            <tr><td>Age</td><td>${v('groom_age')}</td><td>${v('bride_age')}</td></tr>
            <tr><td>Nationality</td><td>${v('groom_citizenship')}</td><td>${v('bride_citizenship')}</td></tr>
            <tr><td>Name of Mother</td><td>$groomMother</td><td>$brideMother</td></tr>
            <tr><td>Name of Father</td><td>$groomFather</td><td>$brideFather</td></tr>
          </tbody>
        </table>
      ''';
    }

    // Resolve header/footer fields per form type
    final cityVal     = type == 'marriage-license' ? v('city_municipality') : v('city');
    final dateVal     = type == 'marriage-license' ? v('date_issuance')     : v('date');
    final issuedTo    = v('issued_to');
    final verifiedBy  = v('verified_by');
    final verifiedPos = v('verified_position');
    final amountPaid  = v('amount_paid');
    final orNumber    = v('or_number');
    final datePaid    = v('date_paid');

    // Assemble full HTML
    final html = '''<!DOCTYPE html><html><head>
<title>LCR Form No. $formNo</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 13px; color: #111; background:#fff; padding: 36px 52px; line-height:1.6; }
@page { size: A4; margin: 14mm 16mm; }

.ph { display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2px solid #333; padding-bottom:12px; margin-bottom:16px; }
.ph-ref { font-size:11px; color:#444; line-height:1.6; min-width:110px; }
.ph-title { flex:1; text-align:center; padding:0 16px; }
.ph-office { font-size:17px; font-weight:bold; }
.ph-city { font-size:13px; font-weight:600; min-height:18px; border-bottom:1px solid #333; display:inline-block; min-width:160px; }
.ph-date { font-size:13px; text-align:right; min-width:110px; display:flex; align-items:baseline; gap:6px; justify-content:flex-end; }
.pv-inline { display:inline-block; border-bottom:1px solid #333; min-width:100px; font-weight:600; }

.psalutation { margin-bottom:14px; font-size:13px; }
.psalutation p { text-indent:2em; margin-top:5px; }

.pfields { margin-bottom:16px; }
.pr { display:flex; align-items:baseline; padding:4px 0; border-bottom:1px dotted #ccc; }
.pl { min-width:230px; flex-shrink:0; color:#444; }
.pc { padding:0 10px; color:#666; flex-shrink:0; }
.pv { flex:1; font-weight:600; border-bottom:1px solid #333; min-width:80px; display:block; }

.ptable { width:100%; border-collapse:collapse; margin:12px 0 16px; }
.ptable th { background:#2c3e50; color:white; padding:7px 12px; text-align:center; }
.ptable td { border:1px solid #bbb; padding:5px 12px; }
.ptable td:first-child { background:#f5f5f5; color:#444; width:170px; font-size:12px; }

.pissue { padding:14px 0; font-size:13px; border-top:1px solid #ddd; }
.pv-issue { display:inline-block; border-bottom:1px solid #333; min-width:220px; font-weight:600; }

.pbottom { display:flex; justify-content:space-between; align-items:flex-start; padding:20px 0 16px; border-top:1px solid #ddd; margin-top:8px; gap:40px; }
.pbottom-left { flex:1; }
.psig-lbl { font-size:12px; color:#555; margin-bottom:28px; display:block; }
.psig-line { display:inline-block; border-bottom:1.5px solid #333; min-width:240px; padding-bottom:2px; font-size:13px; font-weight:600; margin-bottom:6px; }
.pbottom-right { font-size:13px; min-width:200px; }
.ppay { display:flex; gap:8px; padding:3px 0; }
.ppay span:first-child { min-width:100px; color:#555; }
.ppay .pv-inline { min-width:90px; }

.pnote { margin-top:20px; font-size:11px; color:#777; font-style:italic; border-top:1px solid #eee; padding-top:10px; }

@media print {
  body { padding: 0; }
  .no-print { display: none !important; }
}
</style>
</head><body>

<div class="ph">
  <div class="ph-ref">LCR Form No. $formNo<br><small>$formName</small></div>
  <div class="ph-title">
    <div>Republic of the Philippines</div>
    <div class="ph-office">Office of the Municipal Registrar</div>
    <div><span class="ph-city">$cityVal</span></div>
  </div>
  <div class="ph-date"><span>Date:</span><span class="pv-inline">$dateVal</span></div>
</div>

<div class="psalutation">
  <strong>TO WHOM IT MAY CONCERN:</strong>
  <p>$salutation</p>
</div>

<div class="pfields">$fieldsHtml</div>

<div class="pissue">
  This certification is issued to <span class="pv-issue">$issuedTo</span> upon his/her request.
</div>

<div class="pbottom">
  <div class="pbottom-left">
    <span class="psig-lbl">Verified by:</span>
    <div class="psig-line">$verifiedBy</div>
    <div class="psig-line" style="font-size:12px;font-weight:normal;">$verifiedPos</div>
  </div>
  <div class="pbottom-right">
    <div class="ppay"><span>Amount Paid</span><span>:</span><span class="pv-inline">$amountPaid</span></div>
    <div class="ppay"><span>OR Number</span><span>:</span><span class="pv-inline">$orNumber</span></div>
    <div class="ppay"><span>Date Paid</span><span>:</span><span class="pv-inline">$datePaid</span></div>
  </div>
</div>

<div class="pnote">Note: A mark, erasure or alteration of any entry invalidates this certification.</div>

<div class="no-print" style="margin-top:24px; text-align:center;">
  <button onclick="window.print()" style="padding:10px 32px;background:#1ec77c;color:white;border:none;border-radius:6px;font-size:14px;font-weight:bold;cursor:pointer;">🖨 Print</button>
  <button onclick="window.close()" style="margin-left:12px;padding:10px 24px;background:#eee;border:none;border-radius:6px;font-size:14px;cursor:pointer;">Close</button>
</div>

</body></html>''';

    try {
      final tempDir  = await getTemporaryDirectory();
      final fileName = 'lcr_form_${formNo}_\${DateTime.now().millisecondsSinceEpoch}.html';
      final file     = File(p.join(tempDir.path, fileName));
      await file.writeAsString(html, encoding: utf8);
      final uri = Uri.file(file.path);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      }
    } catch (_) {
      // print failed silently
    }
  }
}