import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/record_detail_dialog.dart';

class RecordsScreen extends StatefulWidget {
  const RecordsScreen({super.key});

  @override
  State<RecordsScreen> createState() => _RecordsScreenState();
}

class _RecordsScreenState extends State<RecordsScreen> {
  List<dynamic> _records    = [];
  List<dynamic> _filtered   = [];
  bool _loading             = true;
  String _filterType        = 'all';
  String _filterStatus      = 'all';
  String _filterDate        = 'all';
  final _searchCtrl         = TextEditingController();

  // Track which rows are currently being updated (prevent double-tap)
  final Set<dynamic> _updatingIds = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  // ── Fetch from API, then apply client-side filters ────────────
  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final data = await ApiService.getRecords(
        type:   _filterType == 'all' ? null : _filterType,
        search: _searchCtrl.text.trim().isEmpty ? null : _searchCtrl.text.trim(),
        status: _filterStatus == 'all' ? null : _filterStatus,
      );
      setState(() {
        _records  = data;
        _filtered = _applyLocalFilters(data);
      });
    } catch (_) {
      setState(() { _records = []; _filtered = []; });
    } finally {
      setState(() => _loading = false);
    }
  }

  // ── Only date filter is handled client-side ───────────────────
  List<dynamic> _applyLocalFilters(List<dynamic> data) {
    if (_filterDate == 'all') return data;
    final now = DateTime.now();
    return data.where((r) {
      final date = r['date']?.toString() ?? '';
      try {
        final d = DateTime.parse(date);
        if (_filterDate == 'today' && !_sameDay(d, now))        return false;
        if (_filterDate == 'week'  && now.difference(d).inDays > 7)   return false;
        if (_filterDate == 'month' && now.difference(d).inDays > 30)  return false;
        if (_filterDate == 'year'  && d.year != now.year)        return false;
      } catch (_) { return false; }
      return true;
    }).toList();
  }

  bool _sameDay(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month && a.day == b.day;

  void _clearFilters() {
    _searchCtrl.clear();
    setState(() {
      _filterType   = 'all';
      _filterStatus = 'all';
      _filterDate   = 'all';
    });
    _load();
  }

  // ── Update status for a single record ─────────────────────────
  Future<void> _updateStatus(dynamic record, String newStatus) async {
    final docId = record['doc_id'];
    if (_updatingIds.contains(docId)) return;
    setState(() => _updatingIds.add(docId));

    try {
      final res = await ApiService.updateStatus(docId, newStatus);
      if (res['status'] == 'success') {
        // Update the record locally so UI reflects change immediately
        setState(() {
          for (final r in _records) {
            if (r['doc_id'] == docId) r['status'] = newStatus;
          }
          _filtered = _applyLocalFilters(_records);
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('Record ${newStatus.toLowerCase()} successfully.'),
            backgroundColor: newStatus == 'Approved'
                ? AppTheme.successGreen
                : AppTheme.errorRed,
            duration: const Duration(seconds: 2),
          ));
        }
      } else {
        _showError(res['message'] ?? 'Failed to update status.');
      }
    } catch (_) {
      _showError('Network error. Please try again.');
    } finally {
      setState(() => _updatingIds.remove(docId));
    }
  }

  void _showError(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: AppTheme.errorRed,
      duration: const Duration(seconds: 3),
    ));
  }

  // ── Confirm dialog before status change ───────────────────────
  Future<void> _confirmStatusChange(dynamic record, String newStatus) async {
    final color  = newStatus == 'Approved' ? AppTheme.successGreen : AppTheme.errorRed;
    final icon   = newStatus == 'Approved' ? Icons.check_circle_outline : Icons.cancel_outlined;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        title: Row(children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(width: 8),
          Text('$newStatus Record',
              style: TextStyle(fontWeight: FontWeight.w700, color: color, fontSize: 17)),
        ]),
        content: Text(
          'Are you sure you want to mark this record as $newStatus?\n\n'
          '"${record['name'] ?? record['id']}"',
          style: const TextStyle(fontSize: 14),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel', style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: color),
            child: Text(newStatus,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
    if (confirmed == true) _updateStatus(record, newStatus);
  }

  Color _statusColor(String s) {
    switch (s.toLowerCase()) {
      case 'approved': return AppTheme.successGreen;
      case 'rejected': return AppTheme.errorRed;
      default:         return AppTheme.gold;
    }
  }

  Color _typeColor(String t) {
    switch (t) {
      case 'birth':            return const Color(0xFF3498DB);
      case 'death':            return const Color(0xFF9B59B6);
      case 'marriage-cert':    return AppTheme.primaryGreen;
      case 'marriage-license': return AppTheme.gold;
      default:                 return Colors.grey;
    }
  }

  String _typeLabel(String t) {
    switch (t) {
      case 'birth':            return 'Birth';
      case 'death':            return 'Death';
      case 'marriage-cert':    return 'Marriage Cert';
      case 'marriage-license': return 'Marriage License';
      default:                 return t;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 28),
      child: Column(crossAxisAlignment: CrossAxisAlignment.center, children: [

        // ── Title ────────────────────────────────────────────
        const Text('RECORDS',
            style: TextStyle(fontSize: 32, fontWeight: FontWeight.w900,
                color: AppTheme.navy, letterSpacing: 2)),
        const SizedBox(height: 28),

        // ── Filter card ───────────────────────────────────────
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 20),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.06),
                blurRadius: 12, offset: const Offset(0, 2))],
          ),
          child: Column(children: [
            // Search row
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              SizedBox(
                width: 380,
                child: TextField(
                  controller: _searchCtrl,
                  decoration: InputDecoration(
                    hintText: 'Search by name or ID...',
                    hintStyle: TextStyle(color: Colors.grey[400], fontSize: 14),
                    prefixIcon: const Icon(Icons.search, size: 18, color: Colors.grey),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: BorderSide(color: Colors.grey.shade300),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: BorderSide(color: Colors.grey.shade300),
                    ),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                  onSubmitted: (_) => _load(),
                ),
              ),
              const SizedBox(width: 12),
              SizedBox(
                height: 48,
                child: ElevatedButton.icon(
                  onPressed: _load,
                  icon: const Icon(Icons.search, size: 18),
                  label: const Text('Search',
                      style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                  ),
                ),
              ),
            ]),
            const SizedBox(height: 16),

            // Filter dropdowns row
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              _Dropdown(
                value: _filterType,
                items: const {
                  'all':              'All Types',
                  'birth':            'Birth',
                  'death':            'Death',
                  'marriage-cert':    'Marriage Cert',
                  'marriage-license': 'Marriage License',
                },
                onChanged: (v) {
                  setState(() => _filterType = v!);
                  _load();
                },
              ),
              const SizedBox(width: 12),
              _Dropdown(
                value: _filterStatus,
                items: const {
                  'all':      'All Status',
                  'Pending':  'Pending',
                  'Approved': 'Approved',
                  'Rejected': 'Rejected',
                },
                onChanged: (v) {
                  setState(() => _filterStatus = v!);
                  _load();
                },
              ),
              const SizedBox(width: 12),
              _Dropdown(
                value: _filterDate,
                items: const {
                  'all':   'All Dates',
                  'today': 'Today',
                  'week':  'This Week',
                  'month': 'This Month',
                  'year':  'This Year',
                },
                onChanged: (v) {
                  setState(() {
                    _filterDate = v!;
                    _filtered   = _applyLocalFilters(_records);
                  });
                  // Date filter is local-only — no need to re-fetch
                },
              ),
              const SizedBox(width: 12),
              SizedBox(
                height: 46,
                child: ElevatedButton(
                  onPressed: _clearFilters,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF555555),
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                  ),
                  child: const Text('Clear Filters',
                      style: TextStyle(fontWeight: FontWeight.w600)),
                ),
              ),
            ]),
          ]),
        ),

        // ── Results count ─────────────────────────────────────
        if (!_loading) ...[
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerLeft,
            child: Text(
              '${_filtered.length} record${_filtered.length == 1 ? '' : 's'} found',
              style: TextStyle(fontSize: 13, color: Colors.grey[500]),
            ),
          ),
        ],
        const SizedBox(height: 8),

        // ── Table ─────────────────────────────────────────────
        Expanded(
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : _filtered.isEmpty
                  ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.inbox_outlined, size: 56, color: Colors.grey[300]),
                        const SizedBox(height: 12),
                        Text('No records found.',
                            style: TextStyle(color: Colors.grey[400], fontSize: 15)),
                      ]))
                  : Container(
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05),
                            blurRadius: 10, offset: const Offset(0, 2))],
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: SingleChildScrollView(
                          child: DataTable(
                            headingRowColor: WidgetStateProperty.all(AppTheme.lightGreen),
                            headingTextStyle: const TextStyle(
                                fontWeight: FontWeight.w700,
                                color: AppTheme.navy,
                                fontSize: 13),
                            dataRowMinHeight: 56,
                            dataRowMaxHeight: 56,
                            columnSpacing: 20,
                            columns: const [
                              DataColumn(label: Text('ID')),
                              DataColumn(label: Text('Name')),
                              DataColumn(label: Text('Type')),
                              DataColumn(label: Text('Status')),
                              DataColumn(label: Text('Date')),
                              DataColumn(label: Text('Actions')),
                            ],
                            rows: _filtered.map((r) {
                              final type      = r['type']   ?? '';
                              final status    = (r['status'] ?? '').toString();
                              final docId     = r['doc_id'];
                              final isUpdating = _updatingIds.contains(docId);
                              final isPending  = status.toLowerCase() == 'pending';

                              return DataRow(cells: [
                                DataCell(Text('#${r['id']}',
                                    style: TextStyle(fontSize: 12, color: Colors.grey[500]))),
                                DataCell(Text(r['name'] ?? '\u2014',
                                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13))),
                                DataCell(_Badge(
                                  label: _typeLabel(type),
                                  color: _typeColor(type),
                                )),
                                DataCell(_Badge(
                                  label: status,
                                  color: _statusColor(status),
                                )),
                                DataCell(Text(r['date'] ?? '\u2014',
                                    style: TextStyle(fontSize: 13, color: Colors.grey[600]))),

                                // ── Actions cell ──────────────────────────────
                                DataCell(
                                  isUpdating
                                      ? const SizedBox(
                                          width: 20, height: 20,
                                          child: CircularProgressIndicator(strokeWidth: 2))
                                      : Row(mainAxisSize: MainAxisSize.min, children: [
                                          // View button — always visible
                                          _ActionButton(
                                            label: 'View',
                                            icon: Icons.visibility_outlined,
                                            color: AppTheme.primaryGreen,
                                            onTap: () => showDialog(
                                              context: context,
                                              builder: (_) => RecordDetailDialog(record: r),
                                            ).then((_) => _load()),
                                          ),

                                          // Approve / Reject — only for Pending records
                                          if (isPending) ...[
                                            const SizedBox(width: 6),
                                            _ActionButton(
                                              label: 'Approve',
                                              icon: Icons.check_circle_outline,
                                              color: AppTheme.successGreen,
                                              onTap: () => _confirmStatusChange(r, 'Approved'),
                                            ),
                                            const SizedBox(width: 6),
                                            _ActionButton(
                                              label: 'Reject',
                                              icon: Icons.cancel_outlined,
                                              color: AppTheme.errorRed,
                                              onTap: () => _confirmStatusChange(r, 'Rejected'),
                                            ),
                                          ],

                                          // Re-open option for already-decided records
                                          if (!isPending) ...[
                                            const SizedBox(width: 6),
                                            _ActionButton(
                                              label: 'Pending',
                                              icon: Icons.refresh_outlined,
                                              color: AppTheme.gold,
                                              onTap: () => _confirmStatusChange(r, 'Pending'),
                                            ),
                                          ],
                                        ]),
                                ),
                              ]);
                            }).toList(),
                          ),
                        ),
                      ),
                    ),
        ),
      ]),
    );
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }
}

// ── Small icon + label action button ─────────────────────────
class _ActionButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _ActionButton({
    required this.label,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: label,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(6),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
          decoration: BoxDecoration(
            color: color.withOpacity(0.08),
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: color.withOpacity(0.3)),
          ),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            Icon(icon, size: 14, color: color),
            const SizedBox(width: 4),
            Text(label,
                style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.w600)),
          ]),
        ),
      ),
    );
  }
}

// ── Reusable dropdown ─────────────────────────────────────────
class _Dropdown extends StatelessWidget {
  final String value;
  final Map<String, String> items;
  final ValueChanged<String?> onChanged;

  const _Dropdown({
    required this.value,
    required this.items,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 46,
      padding: const EdgeInsets.symmetric(horizontal: 14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          style: const TextStyle(fontSize: 13, color: Colors.black87,
              fontFamily: 'Poppins'),
          icon: const Icon(Icons.keyboard_arrow_down, size: 18),
          items: items.entries.map((e) => DropdownMenuItem(
            value: e.key,
            child: Text(e.value),
          )).toList(),
          onChanged: onChanged,
        ),
      ),
    );
  }
}

// ── Colored badge ─────────────────────────────────────────────
class _Badge extends StatelessWidget {
  final String label;
  final Color color;

  const _Badge({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.35)),
      ),
      child: Text(label,
          style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.w700)),
    );
  }
}