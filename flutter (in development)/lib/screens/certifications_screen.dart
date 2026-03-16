import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:desktop_drop/desktop_drop.dart';
import 'dart:convert';
import '../theme.dart';
import '../services/api_service.dart';

class CertificationsScreen extends StatefulWidget {
  const CertificationsScreen({super.key});

  @override
  State<CertificationsScreen> createState() => _CertificationsScreenState();
}

class _CertificationsScreenState extends State<CertificationsScreen> {
  PlatformFile? _selectedFile;
  bool _processing = false;
  bool _dragging   = false;
  String? _error;

  Map<String, dynamic>? _resultFields;
  String? _formClass;
  String? _docType;   // 'birth' | 'death' | 'marriage-cert'
  String? _rawText;
  int?    _userId;
  bool    _saving = false;
  bool    _saved  = false;

  // ── File selection ────────────────────────────────────────
  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'jpg', 'jpeg', 'png'],
      withData: true,
    );
    if (result != null && result.files.isNotEmpty) {
      _setFile(result.files.first);
    }
  }

  void _setFile(PlatformFile file) {
    setState(() {
      _selectedFile = file;
      _resultFields = null;
      _formClass    = null;
      _saved        = false;
      _error        = null;
    });
  }

  // ── Process / upload ──────────────────────────────────────
  Future<void> _process() async {
    if (_selectedFile == null) {
      setState(() => _error = 'Please select a file first.');
      return;
    }
    setState(() { _processing = true; _error = null; });

    try {
      final bytes = _selectedFile!.bytes!;
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('${ApiService.baseUrl}/php/process_upload.php'),
      );
      request.files.add(http.MultipartFile.fromBytes(
        'file', bytes, filename: _selectedFile!.name,
      ));
      request.fields['type'] = 'birth';

      final streamed = await request.send();
      final response = await http.Response.fromStream(streamed);
      final data     = json.decode(response.body);

      if (data['status'] == 'success') {
        setState(() {
          _formClass    = data['form_class'];
          _docType      = data['type']?.toString();
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

  // ── Save ─────────────────────────────────────────────────
  Future<void> _saveRecord() async {
    if (_resultFields == null) return;
    setState(() { _saving = true; _error = null; });
    try {
      final result = await ApiService.saveRecord(
        _resultFields!,
        type:    _docType,
        rawText: _rawText,
      );
      // user_id is read from SharedPreferences inside ApiService.saveRecord
      if (result['status'] == 'success') {
        setState(() => _saved = true);
      } else {
        setState(() => _error = result['message'] ?? 'Save failed.');
      }
    } catch (e) {
      setState(() => _error = 'Connection error.');
    } finally {
      setState(() => _saving = false);
    }
  }

  void _reset() => setState(() {
    _selectedFile = null;
    _resultFields = null;
    _formClass    = null;
    _docType      = null;
    _rawText      = null;
    _userId       = null;
    _saved        = false;
    _error        = null;
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('CERTIFICATIONS'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(32),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 700),
            child: _resultFields != null ? _buildResultView() : _buildUploadView(),
          ),
        ),
      ),
    );
  }

  // ── Upload view ───────────────────────────────────────────
  Widget _buildUploadView() {
    return Column(crossAxisAlignment: CrossAxisAlignment.center, children: [
      const Text('Upload Document',
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppTheme.navy)),
      const SizedBox(height: 8),
      Text('Drag & drop or click to browse — PDF, JPG, PNG',
          style: TextStyle(fontSize: 13, color: Colors.grey[500])),
      const SizedBox(height: 32),

      // ── Drag & drop zone ───────────────────────────────
      DropTarget(
        onDragDone: (detail) async {
          final xfile = detail.files.first;
          final bytes = await xfile.readAsBytes();
          _setFile(PlatformFile(
            name:  xfile.name,
            size:  bytes.length,
            bytes: bytes,
            path:  xfile.path,
          ));
        },
        onDragEntered: (_) => setState(() => _dragging = true),
        onDragExited:  (_) => setState(() => _dragging = false),
        child: GestureDetector(
          onTap: _pickFile,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            width: double.infinity,
            height: 220,
            decoration: BoxDecoration(
              border: Border.all(
                color: _dragging
                    ? AppTheme.darkGreen
                    : _selectedFile != null
                        ? AppTheme.primaryGreen
                        : AppTheme.primaryGreen.withOpacity(0.4),
                width: _dragging ? 3 : 2,
                style: BorderStyle.solid,
              ),
              borderRadius: BorderRadius.circular(16),
              color: _dragging
                  ? AppTheme.lightGreen
                  : _selectedFile != null
                      ? AppTheme.lightGreen
                      : AppTheme.paleGreen,
              boxShadow: _dragging
                  ? [BoxShadow(color: AppTheme.primaryGreen.withOpacity(0.2), blurRadius: 16)]
                  : [],
            ),
            child: _selectedFile == null
                ? Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                    AnimatedScale(
                      scale: _dragging ? 1.2 : 1.0,
                      duration: const Duration(milliseconds: 150),
                      child: Icon(
                        _dragging ? Icons.file_download : Icons.upload_file,
                        size: 52,
                        color: _dragging
                            ? AppTheme.primaryGreen
                            : AppTheme.primaryGreen.withOpacity(0.5),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      _dragging ? 'Drop to upload!' : 'Drag & drop file here',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: _dragging ? FontWeight.w700 : FontWeight.normal,
                        color: _dragging ? AppTheme.darkGreen : Colors.grey,
                      ),
                    ),
                    const SizedBox(height: 6),
                    if (!_dragging) ...[
                      Text('or', style: TextStyle(fontSize: 12, color: Colors.grey[400])),
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryGreen.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: AppTheme.primaryGreen.withOpacity(0.3)),
                        ),
                        child: const Text('Browse Files',
                            style: TextStyle(color: AppTheme.primaryGreen,
                                fontWeight: FontWeight.w600, fontSize: 13)),
                      ),
                    ],
                  ])
                : Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                    const Icon(Icons.check_circle, size: 44, color: AppTheme.primaryGreen),
                    const SizedBox(height: 12),
                    Text(_selectedFile!.name,
                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                    const SizedBox(height: 4),
                    Text(_formatSize(_selectedFile!.size),
                        style: TextStyle(fontSize: 12, color: Colors.grey[500])),
                    const SizedBox(height: 10),
                    TextButton.icon(
                      onPressed: _pickFile,
                      icon: const Icon(Icons.swap_horiz, size: 14),
                      label: const Text('Change file'),
                      style: TextButton.styleFrom(foregroundColor: AppTheme.primaryGreen),
                    ),
                  ]),
          ),
        ),
      ),

      // Error
      if (_error != null) ...[
        const SizedBox(height: 16),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFFFDEDED),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(children: [
            const Icon(Icons.error_outline, color: AppTheme.errorRed, size: 16),
            const SizedBox(width: 8),
            Expanded(child: Text(_error!,
                style: const TextStyle(color: AppTheme.errorRed, fontSize: 13))),
          ]),
        ),
      ],

      const SizedBox(height: 24),
      SizedBox(
        width: 200, height: 48,
        child: ElevatedButton(
          onPressed: (_processing || _selectedFile == null) ? null : _process,
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
    ]);
  }

  // ── Result / review view ──────────────────────────────────
  Widget _buildResultView() {
    final formLabel = _formClass == '1A' ? 'Form 1A — Birth Certificate'
                    : _formClass == '2A' ? 'Form 2A — Death Certificate'
                    : _formClass == '3A' ? 'Form 3A — Marriage Certificate'
                    : 'Form 90 — Marriage License';

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Review Extracted Data',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppTheme.navy)),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: AppTheme.lightGreen,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(formLabel,
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                    color: AppTheme.darkGreen)),
          ),
        ])),
        TextButton.icon(
          onPressed: _reset,
          icon: const Icon(Icons.arrow_back, size: 16),
          label: const Text('Upload Another'),
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
            border: Border.all(color: AppTheme.successGreen.withOpacity(0.4)),
          ),
          child: Row(children: [
            const Icon(Icons.check_circle, color: AppTheme.successGreen, size: 18),
            const SizedBox(width: 10),
            const Expanded(child: Text('Record saved successfully!',
                style: TextStyle(color: AppTheme.successGreen, fontWeight: FontWeight.w600))),
            TextButton(onPressed: _reset, child: const Text('New Upload')),
          ]),
        ),

      Card(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Wrap(
            spacing: 16,
            runSpacing: 4,
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
          const SizedBox(width: 12),
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
                style: const TextStyle(fontWeight: FontWeight.w700, letterSpacing: 0.5)),
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