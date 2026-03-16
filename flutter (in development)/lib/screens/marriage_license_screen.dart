import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:desktop_drop/desktop_drop.dart';
import 'dart:convert';
import '../theme.dart';
import '../services/api_service.dart';
import '../services/print_service.dart';

class MarriageLicenseScreen extends StatefulWidget {
  const MarriageLicenseScreen({super.key});

  @override
  State<MarriageLicenseScreen> createState() => _MarriageLicenseScreenState();
}

class _MarriageLicenseScreenState extends State<MarriageLicenseScreen> {
  PlatformFile? _groomFile;
  PlatformFile? _brideFile;
  bool _processing = false;
  bool _draggingGroom = false;
  bool _draggingBride = false;
  String? _error;

  Map<String, dynamic>? _resultFields;
  String? _rawText;
  int?    _userId;
  bool  _saving = false;
  bool  _saved  = false;

  // Both files required before proceeding
  bool get _canProceed => _groomFile != null && _brideFile != null && !_processing;

  Future<void> _pickFile(bool isGroom) async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'jpg', 'jpeg', 'png'],
      withData: true,
    );
    if (result != null && result.files.isNotEmpty) {
      setState(() {
        if (isGroom) _groomFile = result.files.first;
        else         _brideFile = result.files.first;
        _resultFields = null;
        _saved = false; _error = null;
      });
    }
  }

  void _clearFile(bool isGroom) {
    setState(() {
      if (isGroom) _groomFile = null;
      else         _brideFile = null;
      _resultFields = null;
      _saved = false; _error = null;
    });
  }

  Future<void> _process() async {
    if (!_canProceed) {
      setState(() => _error = 'Please upload both Groom and Bride files before proceeding.');
      return;
    }
    setState(() { _processing = true; _error = null; });
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('${ApiService.baseUrl}/php/process_upload.php'),
      );
      // Send groom as 'file' (primary) and bride as 'file2'
      request.files.add(http.MultipartFile.fromBytes(
        'file', _groomFile!.bytes!, filename: _groomFile!.name,
      ));
      request.files.add(http.MultipartFile.fromBytes(
        'file2', _brideFile!.bytes!, filename: _brideFile!.name,
      ));
      request.fields['type'] = 'marriage-license';

      final streamed = await request.send();
      final response = await http.Response.fromStream(streamed);
      final data     = json.decode(response.body);

      if (data['status'] == 'success') {
        setState(() {
          _rawText      = data['raw_text']?.toString();
          _userId       = data['user_id'] is int ? data['user_id'] : int.tryParse(data['user_id']?.toString() ?? '');
          _resultFields = Map<String, dynamic>.from(data['fields'] ?? {});
        });
      } else {
        setState(() => _error = data['message'] ?? 'Processing failed.');
      }
    } catch (e) {
      setState(() => _error = 'Error: $e');
    } finally {
      setState(() => _processing = false);
    }
  }

  Future<void> _saveRecord() async {
    if (_resultFields == null) return;
    setState(() { _saving = true; _error = null; });
    try {
      final result = await ApiService.saveRecord(
        _resultFields!,
        type:    'marriage-license',
        rawText: _rawText,
      );
      if (result['status'] == 'success') setState(() => _saved = true);
      else setState(() => _error = result['message'] ?? 'Save failed.');
    } catch (e) {
      setState(() => _error = 'Connection error.');
    } finally {
      setState(() => _saving = false);
    }
  }

  void _reset() => setState(() {
    _groomFile = null; _brideFile = null;
    _resultFields = null; _rawText = null; _userId = null;
    _saved = false; _error = null;
  });

  Future<void> _print() async {
    if (_resultFields == null) return;
    await PrintService.printRecord({
      'type':     'marriage-license',
      'id':       '',
      'status':   _saved ? 'Approved' : 'Pending',
      'formData': _resultFields,
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('APPLICATION FOR MARRIAGE LICENSE'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(32),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 900),
            child: _resultFields != null ? _buildResultView() : _buildUploadView(),
          ),
        ),
      ),
    );
  }

  Widget _buildUploadView() {
    return Column(crossAxisAlignment: CrossAxisAlignment.center, children: [
      const Text('Upload Marriage License',
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppTheme.navy)),
      const SizedBox(height: 8),
      Text('Upload Form 90 \u2014 one page per applicant (PDF, JPG, PNG)',
          style: TextStyle(fontSize: 13, color: Colors.grey[500])),
      const SizedBox(height: 32),

      // ── Side-by-side drop zones ────────────────────────────────
      IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // GROOM — left
            Expanded(
              child: _buildDropZone(
                label: 'GROOM',
                sublabel: 'Form 90 \u2014 Groom page (Required)',
                icon: Icons.man,
                accentColor: const Color(0xFF3498DB),
                file: _groomFile,
                dragging: _draggingGroom,
                isGroom: true,
              ),
            ),
            const SizedBox(width: 20),
            // BRIDE — right
            Expanded(
              child: _buildDropZone(
                label: 'BRIDE',
                sublabel: 'Form 90 \u2014 Bride page (Required)',
                icon: Icons.woman,
                accentColor: const Color(0xFFE91E8C),
                file: _brideFile,
                dragging: _draggingBride,
                isGroom: false,
              ),
            ),
          ],
        ),
      ),

      // ── Both required notice ───────────────────────────────────
      const SizedBox(height: 12),
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: const Color(0xFFFFF8E1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: AppTheme.gold.withOpacity(0.4)),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(Icons.info_outline, size: 15, color: AppTheme.gold),
          const SizedBox(width: 8),
          Text(
            'Both Groom and Bride files are required to proceed.',
            style: TextStyle(fontSize: 12, color: Colors.brown[700], fontWeight: FontWeight.w500),
          ),
        ]),
      ),

      if (_error != null) ...[
        const SizedBox(height: 16),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
              color: const Color(0xFFFDEDED),
              borderRadius: BorderRadius.circular(8)),
          child: Row(children: [
            const Icon(Icons.error_outline, color: AppTheme.errorRed, size: 16),
            const SizedBox(width: 8),
            Expanded(child: Text(_error!,
                style: const TextStyle(color: AppTheme.errorRed, fontSize: 13))),
          ]),
        ),
      ],

      const SizedBox(height: 28),
      SizedBox(
        width: 220, height: 50,
        child: ElevatedButton(
          onPressed: _canProceed ? _process : null,
          style: ElevatedButton.styleFrom(
            disabledBackgroundColor: Colors.grey[300],
            disabledForegroundColor: Colors.grey[500],
          ),
          child: _processing
              ? const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                  SizedBox(width: 18, height: 18,
                      child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)),
                  SizedBox(width: 10),
                  Text('Processing...'),
                ])
              : const Text('PROCEED',
                  style: TextStyle(fontWeight: FontWeight.w700, letterSpacing: 1)),
        ),
      ),

      // ── Upload status indicators below button ──────────────────
      const SizedBox(height: 12),
      Row(mainAxisAlignment: MainAxisAlignment.center, children: [
        _StatusDot(filled: _groomFile != null, color: const Color(0xFF3498DB), label: 'Groom'),
        const SizedBox(width: 20),
        _StatusDot(filled: _brideFile != null, color: const Color(0xFFE91E8C), label: 'Bride'),
      ]),
    ]);
  }

  Widget _buildDropZone({
    required String label,
    required String sublabel,
    required IconData icon,
    required Color accentColor,
    required PlatformFile? file,
    required bool dragging,
    required bool isGroom,
  }) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      // Label pill
      Row(children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
          decoration: BoxDecoration(
            color: accentColor.withOpacity(0.12),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: accentColor.withOpacity(0.4)),
          ),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            Icon(icon, size: 14, color: accentColor),
            const SizedBox(width: 5),
            Text(label,
                style: TextStyle(
                    fontSize: 12, fontWeight: FontWeight.w700, color: accentColor)),
          ]),
        ),
        const SizedBox(width: 10),
        Text(sublabel, style: TextStyle(fontSize: 12, color: Colors.grey[500])),
      ]),
      const SizedBox(height: 10),

      // Drop target
      DropTarget(
        onDragDone: (detail) async {
          if (detail.files.isNotEmpty) {
            final xf    = detail.files.first;
            final bytes = await xf.readAsBytes();
            final pf = PlatformFile(
              name:  xf.name,
              size:  bytes.length,
              path:  xf.path,
              bytes: bytes,
            );
            setState(() {
              if (isGroom) { _groomFile = pf; _draggingGroom = false; }
              else         { _brideFile = pf; _draggingBride = false; }
              _resultFields = null;
              _saved = false; _error = null;
            });
          }
        },
        onDragEntered: (_) => setState(() {
          if (isGroom) _draggingGroom = true;
          else         _draggingBride = true;
        }),
        onDragExited: (_) => setState(() {
          if (isGroom) _draggingGroom = false;
          else         _draggingBride = false;
        }),
        child: GestureDetector(
          onTap: () => _pickFile(isGroom),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            width: double.infinity,
            height: 160,
            decoration: BoxDecoration(
              border: Border.all(
                color: dragging ? accentColor
                    : file != null ? accentColor.withOpacity(0.7)
                    : accentColor.withOpacity(0.35),
                width: dragging ? 3 : 2,
              ),
              borderRadius: BorderRadius.circular(12),
              color: dragging ? accentColor.withOpacity(0.08)
                  : file != null ? accentColor.withOpacity(0.06)
                  : Colors.grey.shade50,
            ),
            child: file == null
                ? Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                    Icon(dragging ? Icons.file_download : icon,
                        size: 40,
                        color: dragging ? accentColor : accentColor.withOpacity(0.35)),
                    const SizedBox(height: 10),
                    Text(
                      dragging ? 'Drop to upload!' : 'Drag & drop or click to browse',
                      style: TextStyle(
                          fontSize: 13,
                          color: dragging ? accentColor : Colors.grey[500]),
                    ),
                    const SizedBox(height: 4),
                    Text('PDF, JPG, PNG',
                        style: TextStyle(fontSize: 11, color: Colors.grey[400])),
                  ])
                : Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Row(children: [
                          Icon(Icons.check_circle, size: 24, color: accentColor),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(file.name,
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w700, fontSize: 13),
                                    overflow: TextOverflow.ellipsis),
                                Text(_formatSize(file.size),
                                    style: TextStyle(fontSize: 11, color: Colors.grey[500])),
                              ],
                            ),
                          ),
                        ]),
                        const SizedBox(height: 10),
                        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                          OutlinedButton.icon(
                            onPressed: () => _pickFile(isGroom),
                            icon: Icon(Icons.swap_horiz, size: 14, color: accentColor),
                            label: Text('Change',
                                style: TextStyle(fontSize: 12, color: accentColor)),
                            style: OutlinedButton.styleFrom(
                              side: BorderSide(color: accentColor.withOpacity(0.5)),
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              minimumSize: Size.zero,
                            ),
                          ),
                          const SizedBox(width: 8),
                          OutlinedButton.icon(
                            onPressed: () => _clearFile(isGroom),
                            icon: Icon(Icons.close, size: 14, color: Colors.grey[600]),
                            label: Text('Remove',
                                style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                            style: OutlinedButton.styleFrom(
                              side: BorderSide(color: Colors.grey.shade300),
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              minimumSize: Size.zero,
                            ),
                          ),
                        ]),
                      ],
                    ),
                  ),
          ),
        ),
      ),
    ]);
  }

  Widget _buildResultView() {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Review Extracted Data',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppTheme.navy)),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
                color: AppTheme.gold.withOpacity(0.15),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.gold.withOpacity(0.4))),
            child: const Text('Form 90 \u2014 Marriage License',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                    color: AppTheme.gold)),
          ),
        ])),
        TextButton.icon(
          onPressed: _reset,
          icon: const Icon(Icons.arrow_back, size: 16),
          label: const Text('Upload Again'),
        ),
      ]),
      const SizedBox(height: 8),
      Text('Check and correct any fields before saving.',
          style: TextStyle(fontSize: 13, color: Colors.grey[500])),
      const SizedBox(height: 20),

      if (_saved)
        Container(
          width: double.infinity,
          margin: const EdgeInsets.only(bottom: 20),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
              color: const Color(0xFFEBF9F1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppTheme.successGreen.withOpacity(0.4))),
          child: Row(children: [
            const Icon(Icons.check_circle, color: AppTheme.successGreen, size: 18),
            const SizedBox(width: 10),
            const Expanded(child: Text('Record saved successfully!',
                style: TextStyle(color: AppTheme.successGreen, fontWeight: FontWeight.w600))),
            TextButton(onPressed: _print,
                child: const Text('Print Now',
                    style: TextStyle(color: AppTheme.primaryGreen, fontWeight: FontWeight.w600))),
            TextButton(onPressed: _reset, child: const Text('New Upload')),
          ]),
        ),

      Card(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Wrap(
            spacing: 16, runSpacing: 4,
            children: _resultFields!.entries.map((e) => SizedBox(
              width: 290,
              child: _EditableField(
                label: _formatKey(e.key),
                value: e.value?.toString() ?? '',
                onChanged: (v) => _resultFields![e.key] = v,
              ),
            )).toList(),
          ),
        ),
      ),

      if (_error != null) ...[
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
              color: const Color(0xFFFDEDED), borderRadius: BorderRadius.circular(8)),
          child: Text(_error!, style: const TextStyle(color: AppTheme.errorRed)),
        ),
      ],

      if (!_saved) ...[
        const SizedBox(height: 24),
        Row(mainAxisAlignment: MainAxisAlignment.end, children: [
          OutlinedButton(onPressed: _reset, child: const Text('Cancel')),
          const SizedBox(width: 10),
          OutlinedButton.icon(
            onPressed: _print,
            icon: const Icon(Icons.print, size: 16),
            label: const Text('Print Preview'),
            style: OutlinedButton.styleFrom(
                foregroundColor: AppTheme.navy,
                side: const BorderSide(color: AppTheme.navy)),
          ),
          const SizedBox(width: 10),
          ElevatedButton.icon(
            onPressed: _saving ? null : _saveRecord,
            style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.successGreen,
                padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 14)),
            icon: _saving
                ? const SizedBox(width: 16, height: 16,
                    child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                : const Icon(Icons.save, size: 18),
            label: Text(_saving ? 'Saving...' : 'SAVE RECORD',
                style: const TextStyle(fontWeight: FontWeight.w700)),
          ),
        ]),
      ],
    ]);
  }

  String _formatKey(String key) => key.replaceAll('_', ' ').split(' ')
      .map((w) => w.isEmpty ? '' : w[0].toUpperCase() + w.substring(1)).join(' ');

  String _formatSize(int bytes) {
    if (bytes < 1024) return '${bytes}B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)}KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)}MB';
  }
}

// ── Upload status dot indicator ───────────────────────────────
class _StatusDot extends StatelessWidget {
  final bool filled;
  final Color color;
  final String label;
  const _StatusDot({required this.filled, required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(mainAxisSize: MainAxisSize.min, children: [
      AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: 10, height: 10,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: filled ? color : Colors.grey[300],
          border: Border.all(color: filled ? color : Colors.grey.shade400, width: 1.5),
        ),
      ),
      const SizedBox(width: 6),
      Text(label,
          style: TextStyle(
              fontSize: 12,
              color: filled ? color : Colors.grey[400],
              fontWeight: filled ? FontWeight.w600 : FontWeight.normal)),
    ]);
  }
}

// ── Editable field widget ─────────────────────────────────────
class _EditableField extends StatefulWidget {
  final String label;
  final String value;
  final ValueChanged<String> onChanged;
  const _EditableField({required this.label, required this.value, required this.onChanged});

  @override
  State<_EditableField> createState() => _EditableFieldState();
}

class _EditableFieldState extends State<_EditableField> {
  late TextEditingController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: widget.value);
    _ctrl.addListener(() => widget.onChanged(_ctrl.text));
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(widget.label,
            style: TextStyle(fontSize: 11, color: Colors.grey[500], fontWeight: FontWeight.w500)),
        const SizedBox(height: 4),
        TextField(
          controller: _ctrl,
          style: const TextStyle(fontSize: 13),
          decoration: InputDecoration(
            isDense: true,
            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(6)),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(6),
              borderSide: const BorderSide(color: AppTheme.primaryGreen, width: 2),
            ),
            filled: true,
            fillColor: _ctrl.text.isEmpty ? Colors.grey[50] : const Color(0xFFF0FDF7),
          ),
        ),
      ]),
    );
  }
}