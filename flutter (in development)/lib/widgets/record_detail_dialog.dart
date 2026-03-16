import 'package:flutter/material.dart';
import '../theme.dart';
import '../services/api_service.dart';
import '../services/print_service.dart';

class RecordDetailDialog extends StatefulWidget {
  final Map<String, dynamic> record;

  const RecordDetailDialog({super.key, required this.record});

  @override
  State<RecordDetailDialog> createState() => _RecordDetailDialogState();
}

class _RecordDetailDialogState extends State<RecordDetailDialog> {
  bool _editing = false;
  bool _saving  = false;
  String? _saveMessage;
  bool _saveSuccess = false;

  late Map<String, dynamic> _data;
  late Map<String, TextEditingController> _controllers;

  @override
  void initState() {
    super.initState();
    _data = Map<String, dynamic>.from(widget.record['formData'] ?? {});
    _controllers = {};
    for (final key in _data.keys) {
      _controllers[key] = TextEditingController(text: _data[key]?.toString() ?? '');
    }
  }

  @override
  void dispose() {
    for (final c in _controllers.values) c.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() { _saving = true; _saveMessage = null; });
    try {
      // Collect current values from controllers
      final updatedFormData = <String, dynamic>{};
      for (final key in _controllers.keys) {
        updatedFormData[key] = _controllers[key]!.text;
      }

      final result = await ApiService.saveRecord(
        updatedFormData,
        docId: widget.record['doc_id'],
      );

      if (result['status'] == 'success') {
        setState(() {
          _data = updatedFormData;
          _editing = false;
          _saveSuccess = true;
          _saveMessage = 'Record saved successfully.';
        });
      } else {
        setState(() {
          _saveSuccess = false;
          _saveMessage = result['message'] ?? 'Save failed.';
        });
      }
    } catch (e) {
      setState(() {
        _saveSuccess = false;
        _saveMessage = 'Connection error. Is XAMPP running?';
      });
    } finally {
      setState(() => _saving = false);
    }
  }

  void _cancelEdit() {
    // Restore controllers to saved values
    for (final key in _controllers.keys) {
      _controllers[key]!.text = _data[key]?.toString() ?? '';
    }
    setState(() { _editing = false; _saveMessage = null; });
  }

  @override
  Widget build(BuildContext context) {
    final type   = widget.record['type']   ?? '';
    final status = widget.record['status'] ?? '';
    final id     = widget.record['id']     ?? '';

    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        width: 720,
        constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.88),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          // ── Header ────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            decoration: BoxDecoration(
              color: _headerColor(type),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
            ),
            child: Row(children: [
              Icon(_typeIcon(type), color: Colors.white, size: 20),
              const SizedBox(width: 10),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(_formTitle(type), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15)),
                Text('$id  •  $status', style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 12)),
              ])),
              if (_editing)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text('EDITING', style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1)),
                ),
              const SizedBox(width: 8),
              IconButton(icon: const Icon(Icons.close, color: Colors.white), onPressed: () => Navigator.pop(context)),
            ]),
          ),

          // ── Save message banner ───────────────────────────────
          if (_saveMessage != null)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 10),
              color: _saveSuccess ? const Color(0xFFEBF9F1) : const Color(0xFFFDEDED),
              child: Row(children: [
                Icon(_saveSuccess ? Icons.check_circle : Icons.error_outline,
                    size: 16, color: _saveSuccess ? AppTheme.successGreen : AppTheme.errorRed),
                const SizedBox(width: 8),
                Text(_saveMessage!,
                    style: TextStyle(
                        fontSize: 13,
                        color: _saveSuccess ? AppTheme.successGreen : AppTheme.errorRed,
                        fontWeight: FontWeight.w500)),
              ]),
            ),

          // ── Body ──────────────────────────────────────────────
          Flexible(child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: _buildFormContent(type),
          )),

          // ── Footer ────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            decoration: BoxDecoration(border: Border(top: BorderSide(color: Colors.grey.shade200))),
            child: Row(children: [
              if (!_editing) ...[
                const Spacer(),
                OutlinedButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Close'),
                ),
                const SizedBox(width: 10),
                OutlinedButton.icon(
                  onPressed: () async { await PrintService.printRecord(widget.record); },
                  icon: const Icon(Icons.print, size: 16),
                  label: const Text('Print'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppTheme.navy,
                    side: const BorderSide(color: AppTheme.navy),
                  ),
                ),
                const SizedBox(width: 10),
                ElevatedButton.icon(
                  onPressed: () => setState(() { _editing = true; _saveMessage = null; }),
                  icon: const Icon(Icons.edit, size: 16),
                  label: const Text('Edit Record'),
                ),
              ] else ...[
                const Spacer(),
                OutlinedButton(
                  onPressed: _saving ? null : _cancelEdit,
                  child: const Text('Cancel'),
                ),
                const SizedBox(width: 10),
                ElevatedButton.icon(
                  onPressed: _saving ? null : _save,
                  style: ElevatedButton.styleFrom(backgroundColor: AppTheme.successGreen),
                  icon: _saving
                      ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Icon(Icons.save, size: 16),
                  label: Text(_saving ? 'Saving...' : 'Save Changes'),
                ),
              ],
            ]),
          ),
        ]),
      ),
    );
  }

  // ── Form builders ─────────────────────────────────────────
  Widget _buildFormContent(String type) {
    if (type == 'birth')            return _buildBirthForm();
    if (type == 'death')            return _buildDeathForm();
    if (type == 'marriage-license') return _buildMarriageLicenseForm();
    return _buildMarriageCertForm();
  }

  Widget _buildBirthForm() => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    _sectionHeader('Registry Information'),
    _twoCol(_field('Registry Number', 'registry_number'), _field('City/Municipality', 'city')),
    _twoCol(_field('Date of Registration', 'date_of_registration'), _field('Date of Issuance', 'date')),
    const SizedBox(height: 16),
    _sectionHeader('Child Information'),
    _field('Name of Child', 'child_name'),
    _twoCol(_field('Sex', 'sex'), _field('Date of Birth', 'date_of_birth')),
    _field('Place of Birth', 'place_of_birth'),
    const SizedBox(height: 16),
    _sectionHeader("Mother's Information"),
    _field('Name of Mother', 'mother_name'),
    _field('Nationality', 'mother_nationality'),
    const SizedBox(height: 16),
    _sectionHeader("Father's Information"),
    _field('Name of Father', 'father_name'),
    _field('Nationality', 'father_nationality'),
    const SizedBox(height: 16),
    _sectionHeader("Parents' Marriage"),
    _twoCol(_field('Date of Marriage', 'parents_marriage_date'), _field('Place of Marriage', 'parents_marriage_place')),
    const SizedBox(height: 16),
    _sectionHeader('Certification'),
    _twoCol(_field('Issued To', 'issued_to'), _field('Verified By', 'verified_by')),
    _twoCol(_field('Amount Paid', 'amount_paid'), _field('OR Number', 'or_number')),
    _field('Date Paid', 'date_paid'),
  ]);

  Widget _buildDeathForm() => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    _sectionHeader('Registry Information'),
    _twoCol(_field('Registry Number', 'registry_number'), _field('City/Municipality', 'city')),
    _field('Date of Registration', 'date_of_registration'),
    const SizedBox(height: 16),
    _sectionHeader('Deceased Information'),
    _field('Name of Deceased', 'deceased_name'),
    _twoCol(_field('Sex', 'sex'), _field('Age', 'age')),
    _twoCol(_field('Civil Status', 'civil_status'), _field('Nationality', 'nationality')),
    _twoCol(_field('Date of Death', 'date_of_death'), _field('Place of Death', 'place_of_death')),
    _field('Cause of Death', 'cause_of_death'),
    const SizedBox(height: 16),
    _sectionHeader('Certification'),
    _twoCol(_field('Issued To', 'issued_to'), _field('Verified By', 'verified_by')),
    _twoCol(_field('Amount Paid', 'amount_paid'), _field('OR Number', 'or_number')),
  ]);

  Widget _buildMarriageCertForm() => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    _sectionHeader('Registry Information'),
    _twoCol(_field('Registry Number', 'registry_number'), _field('City/Municipality', 'city')),
    _twoCol(_field('Date of Marriage', 'date_of_marriage'), _field('Place of Marriage', 'place_of_marriage')),
    const SizedBox(height: 16),
    Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _sectionHeader('Husband / Groom'),
        _field('Name', 'husband_name'),
        _field('Age', 'husband_age'),
        _field('Nationality', 'husband_nationality'),
        _field('Mother', 'husband_mother_name'),
        _field('Father', 'husband_father_name'),
      ])),
      const SizedBox(width: 16),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _sectionHeader('Wife / Bride'),
        _field('Name', 'wife_name'),
        _field('Age', 'wife_age'),
        _field('Nationality', 'wife_nationality'),
        _field('Mother', 'wife_mother_name'),
        _field('Father', 'wife_father_name'),
      ])),
    ]),
    const SizedBox(height: 16),
    _sectionHeader('Certification'),
    _twoCol(_field('Issued To', 'issued_to'), _field('Verified By', 'verified_by')),
    _twoCol(_field('Amount Paid', 'amount_paid'), _field('OR Number', 'or_number')),
  ]);


  Widget _buildMarriageLicenseForm() => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    _sectionHeader('Registry Information'),
    _twoCol(_field('Registry No', 'registry_no'), _field('License No', 'license_no')),
    _twoCol(_field('City/Municipality', 'city_municipality'), _field('Date of Issuance', 'date_issuance')),
    const SizedBox(height: 16),
    _sectionHeader('Date & Place of Marriage'),
    _twoCol(
      _twoCol(_field('Month', 'marriage_month'), _field('Day', 'marriage_day')),
      _field('Year', 'marriage_year'),
    ),
    _twoCol(_field('Venue', 'marriage_venue'), _field('City', 'marriage_city')),
    const SizedBox(height: 16),
    Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _sectionHeader('Groom'),
        _field('First Name', 'groom_first'),
        _field('Middle Name', 'groom_middle'),
        _field('Last Name', 'groom_last'),
        _field('Age', 'groom_age'),
        _field('Citizenship', 'groom_citizenship'),
        _field('Civil Status', 'groom_civil_status'),
        _field('Residence', 'groom_residence'),
        _field("Mother's First Name", 'groom_mother_first'),
        _field("Mother's Last Name", 'groom_mother_last'),
        _field("Father's First Name", 'groom_father_first'),
        _field("Father's Last Name", 'groom_father_last'),
      ])),
      const SizedBox(width: 16),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _sectionHeader('Bride'),
        _field('First Name', 'bride_first'),
        _field('Middle Name', 'bride_middle'),
        _field('Last Name', 'bride_last'),
        _field('Age', 'bride_age'),
        _field('Citizenship', 'bride_citizenship'),
        _field('Civil Status', 'bride_civil_status'),
        _field('Residence', 'bride_residence'),
        _field("Mother's First Name", 'bride_mother_first'),
        _field("Mother's Last Name", 'bride_mother_last'),
        _field("Father's First Name", 'bride_father_first'),
        _field("Father's Last Name", 'bride_father_last'),
      ])),
    ]),
    const SizedBox(height: 16),
    _sectionHeader('Certification'),
    _twoCol(_field('Issued To', 'issued_to'), _field('Verified By', 'verified_by')),
    _twoCol(_field('Amount Paid', 'amount_paid'), _field('OR Number', 'or_number')),
    _field('Date Paid', 'date_paid'),
  ]);

  // ── UI helpers ────────────────────────────────────────────
  Widget _sectionHeader(String title) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Text(title.toUpperCase(),
        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.primaryGreen, letterSpacing: 1.2)),
  );

  // Key-based field: reads from _controllers in edit mode, shows value in view mode
  Widget _field(String label, String key) {
    if (!_controllers.containsKey(key)) {
      _controllers[key] = TextEditingController(text: _data[key]?.toString() ?? '');
    }
    final displayValue = _data[key]?.toString() ?? '';
    final isEmpty = displayValue.trim().isEmpty;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: TextStyle(fontSize: 11, color: Colors.grey[500])),
        const SizedBox(height: 3),
        if (_editing)
          TextField(
            controller: _controllers[key],
            style: const TextStyle(fontSize: 13),
            decoration: InputDecoration(
              isDense: true,
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(6), borderSide: const BorderSide(color: AppTheme.primaryGreen)),
              focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(6), borderSide: const BorderSide(color: AppTheme.primaryGreen, width: 2)),
              filled: true,
              fillColor: const Color(0xFFF0FDF7),
            ),
          )
        else
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
                color: Colors.grey[50],
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: Colors.grey.shade200)),
            child: Text(isEmpty ? '—' : displayValue,
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: isEmpty ? Colors.grey[400] : Colors.black87)),
          ),
      ]),
    );
  }

  Widget _twoCol(Widget a, Widget b) => Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Expanded(child: a), const SizedBox(width: 12), Expanded(child: b),
  ]);

  Color _headerColor(String type) {
    switch (type) {
      case 'birth': return const Color(0xFF3498DB);
      case 'death': return const Color(0xFF9B59B6);
      case 'marriage-cert': return AppTheme.primaryGreen;
      case 'marriage-license': return AppTheme.gold;
      default: return AppTheme.navy;
    }
  }

  IconData _typeIcon(String type) {
    switch (type) {
      case 'birth': return Icons.child_care;
      case 'death': return Icons.sentiment_very_dissatisfied;
      case 'marriage-cert': return Icons.favorite;
      case 'marriage-license': return Icons.assignment;
      default: return Icons.description;
    }
  }

  String _formTitle(String type) {
    switch (type) {
      case 'birth': return 'LCR Form No. 1A — Birth Certificate';
      case 'death': return 'LCR Form No. 2A — Death Certificate';
      case 'marriage-cert': return 'LCR Form No. 3A — Marriage Certificate';
      case 'marriage-license': return 'LCR Form No. 90 — Marriage License';
      default: return 'Civil Registry Form';
    }
  }
}