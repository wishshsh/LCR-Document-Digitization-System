import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/api_service.dart';
import '../theme.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic> _stats = {};

  // Pie chart touch state
  int _typeTouchedIndex   = -1;
  int _statusTouchedIndex = -1;

  // Colors for document types
  static const _typeColors = [
    Color(0xFF3498DB), // Birth — blue
    Color(0xFF9B59B6), // Death — purple
    Color(0xFF27AE60), // Marriage Cert — green
    Color(0xFFF39C12), // Marriage License — gold
  ];

  // Colors for status
  static const _statusColors = [
    Color(0xFFF39C12), // Pending — gold
    Color(0xFF27AE60), // Approved — green
    Color(0xFFE74C3C), // Rejected — red
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final data = await ApiService.getDashboardStats();
      if (data['status'] == 'success') {
        setState(() => _stats = data);
      } else {
        setState(() => _error = data['message'] ?? 'Failed to load stats.');
      }
    } catch (e) {
      setState(() => _error = 'Connection error. Is XAMPP running?');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 28),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        // ── Header ────────────────────────────────────────────
        Row(children: [
          const Text('DASHBOARD',
              style: TextStyle(fontSize: 32, fontWeight: FontWeight.w900,
                  color: AppTheme.navy, letterSpacing: 2)),
          const Spacer(),
          IconButton(
            onPressed: _load,
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh',
            color: AppTheme.primaryGreen,
          ),
        ]),
        const SizedBox(height: 24),

        if (_loading)
          const Expanded(child: Center(child: CircularProgressIndicator()))
        else if (_error != null)
          Expanded(child: Center(child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error_outline, size: 48, color: Colors.grey[400]),
              const SizedBox(height: 12),
              Text(_error!, style: TextStyle(color: Colors.grey[500])),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _load,
                icon: const Icon(Icons.refresh, size: 16),
                label: const Text('Retry'),
              ),
            ],
          )))
        else
          Expanded(child: _buildContent()),
      ]),
    );
  }

  Widget _buildContent() {
    final total    = _stats['total'] ?? 0;
    final byType   = List<Map<String, dynamic>>.from(
        (_stats['byType'] ?? []).map((e) => Map<String, dynamic>.from(e)));
    final byStatus = List<Map<String, dynamic>>.from(
        (_stats['byStatus'] ?? []).map((e) => Map<String, dynamic>.from(e)));
    final monthly  = List<Map<String, dynamic>>.from(
        (_stats['monthly'] ?? []).map((e) => Map<String, dynamic>.from(e)));
    final recent   = List<Map<String, dynamic>>.from(
        (_stats['recent'] ?? []).map((e) => Map<String, dynamic>.from(e)));

    // Derive stat card values from byStatus
    int pending  = 0, approved = 0, rejected = 0;
    for (final s in byStatus) {
      if (s['label'] == 'Pending')  pending  = s['count'] as int;
      if (s['label'] == 'Approved') approved = s['count'] as int;
      if (s['label'] == 'Rejected') rejected = s['count'] as int;
    }

    return SingleChildScrollView(
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        // ── Stat cards ─────────────────────────────────────────
        Row(children: [
          _StatCard(label: 'Total Records', value: total.toString(),
              icon: Icons.folder_copy_outlined, color: AppTheme.primaryGreen),
          const SizedBox(width: 16),
          _StatCard(label: 'Pending', value: pending.toString(),
              icon: Icons.hourglass_empty_rounded, color: AppTheme.gold),
          const SizedBox(width: 16),
          _StatCard(label: 'Approved', value: approved.toString(),
              icon: Icons.check_circle_outline, color: AppTheme.successGreen),
          const SizedBox(width: 16),
          _StatCard(label: 'Rejected', value: rejected.toString(),
              icon: Icons.cancel_outlined, color: AppTheme.errorRed),
        ]),
        const SizedBox(height: 24),

        // ── Charts row ─────────────────────────────────────────
        IntrinsicHeight(
          child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            // Records by Type — Pie chart
            Expanded(flex: 3, child: _ChartCard(
              title: 'Records by Document Type',
              child: byType.isEmpty
                  ? _emptyChart()
                  : _buildTypePieChart(byType),
            )),
            const SizedBox(width: 16),
            // Records by Status — Pie chart
            Expanded(flex: 3, child: _ChartCard(
              title: 'Records by Status',
              child: byStatus.isEmpty
                  ? _emptyChart()
                  : _buildStatusPieChart(byStatus),
            )),
            const SizedBox(width: 16),
            // Recent activity
            Expanded(flex: 4, child: _ChartCard(
              title: 'Recent Uploads',
              child: recent.isEmpty
                  ? _emptyChart()
                  : _buildRecentList(recent),
            )),
          ]),
        ),
        const SizedBox(height: 24),

        // ── Monthly trend — Line chart ─────────────────────────
        _ChartCard(
          title: 'Monthly Upload Trend (Last 12 Months)',
          height: 260,
          child: monthly.isEmpty
              ? _emptyChart()
              : _buildMonthlyLineChart(monthly),
        ),
      ]),
    );
  }

  // ── Type pie chart ────────────────────────────────────────
  Widget _buildTypePieChart(List<Map<String, dynamic>> data) {
    return Column(children: [
      Expanded(
        child: PieChart(
          PieChartData(
            pieTouchData: PieTouchData(
              touchCallback: (event, response) {
                setState(() {
                  if (!event.isInterestedForInteractions ||
                      response == null || response.touchedSection == null) {
                    _typeTouchedIndex = -1;
                    return;
                  }
                  _typeTouchedIndex =
                      response.touchedSection!.touchedSectionIndex;
                });
              },
            ),
            sectionsSpace: 3,
            centerSpaceRadius: 36,
            sections: data.asMap().entries.map((entry) {
              final i     = entry.key;
              final item  = entry.value;
              final count = (item['count'] as int).toDouble();
              final total = data.fold<double>(0, (s, e) => s + (e['count'] as int));
              final pct   = total > 0 ? (count / total * 100).toStringAsFixed(1) : '0';
              final isTouched = i == _typeTouchedIndex;
              return PieChartSectionData(
                color: _typeColors[i % _typeColors.length],
                value: count == 0 ? 0.001 : count,
                title: isTouched ? '$pct%' : '',
                radius: isTouched ? 64 : 54,
                titleStyle: const TextStyle(
                    fontSize: 12, fontWeight: FontWeight.w700,
                    color: Colors.white),
              );
            }).toList(),
          ),
        ),
      ),
      const SizedBox(height: 12),
      // Legend
      Wrap(
        spacing: 12, runSpacing: 6,
        alignment: WrapAlignment.center,
        children: data.asMap().entries.map((entry) {
          final i    = entry.key;
          final item = entry.value;
          return Row(mainAxisSize: MainAxisSize.min, children: [
            Container(width: 10, height: 10,
                decoration: BoxDecoration(
                  color: _typeColors[i % _typeColors.length],
                  borderRadius: BorderRadius.circular(2),
                )),
            const SizedBox(width: 4),
            Text('${item['label']} (${item['count']})',
                style: TextStyle(fontSize: 11, color: Colors.grey[600])),
          ]);
        }).toList(),
      ),
    ]);
  }

  // ── Status pie chart ──────────────────────────────────────
  Widget _buildStatusPieChart(List<Map<String, dynamic>> data) {
    return Column(children: [
      Expanded(
        child: PieChart(
          PieChartData(
            pieTouchData: PieTouchData(
              touchCallback: (event, response) {
                setState(() {
                  if (!event.isInterestedForInteractions ||
                      response == null || response.touchedSection == null) {
                    _statusTouchedIndex = -1;
                    return;
                  }
                  _statusTouchedIndex =
                      response.touchedSection!.touchedSectionIndex;
                });
              },
            ),
            sectionsSpace: 3,
            centerSpaceRadius: 36,
            sections: data.asMap().entries.map((entry) {
              final i     = entry.key;
              final item  = entry.value;
              final count = (item['count'] as int).toDouble();
              final total = data.fold<double>(0, (s, e) => s + (e['count'] as int));
              final pct   = total > 0 ? (count / total * 100).toStringAsFixed(1) : '0';
              final isTouched = i == _statusTouchedIndex;
              return PieChartSectionData(
                color: _statusColors[i % _statusColors.length],
                value: count == 0 ? 0.001 : count,
                title: isTouched ? '$pct%' : '',
                radius: isTouched ? 64 : 54,
                titleStyle: const TextStyle(
                    fontSize: 12, fontWeight: FontWeight.w700,
                    color: Colors.white),
              );
            }).toList(),
          ),
        ),
      ),
      const SizedBox(height: 12),
      Wrap(
        spacing: 12, runSpacing: 6,
        alignment: WrapAlignment.center,
        children: data.asMap().entries.map((entry) {
          final i    = entry.key;
          final item = entry.value;
          return Row(mainAxisSize: MainAxisSize.min, children: [
            Container(width: 10, height: 10,
                decoration: BoxDecoration(
                  color: _statusColors[i % _statusColors.length],
                  borderRadius: BorderRadius.circular(2),
                )),
            const SizedBox(width: 4),
            Text('${item['label']} (${item['count']})',
                style: TextStyle(fontSize: 11, color: Colors.grey[600])),
          ]);
        }).toList(),
      ),
    ]);
  }

  // ── Monthly line chart ────────────────────────────────────
  Widget _buildMonthlyLineChart(List<Map<String, dynamic>> data) {
    if (data.isEmpty) return _emptyChart();

    final spots = data.asMap().entries.map((entry) =>
        FlSpot(entry.key.toDouble(),
            (entry.value['count'] as int).toDouble())).toList();

    final maxY = data.fold<double>(
        0, (m, e) => (e['count'] as int).toDouble() > m
            ? (e['count'] as int).toDouble() : m);

    return Padding(
      padding: const EdgeInsets.only(right: 24, top: 12, bottom: 4),
      child: LineChart(
        LineChartData(
          minY: 0,
          maxY: maxY + 2,
          gridData: FlGridData(
            show: true,
            drawVerticalLine: false,
            horizontalInterval: maxY > 0 ? (maxY / 4).ceilToDouble() : 1,
            getDrawingHorizontalLine: (_) => FlLine(
              color: Colors.grey.shade200,
              strokeWidth: 1,
            ),
          ),
          borderData: FlBorderData(
            show: true,
            border: Border(
              bottom: BorderSide(color: Colors.grey.shade300),
              left:   BorderSide(color: Colors.grey.shade300),
            ),
          ),
          titlesData: FlTitlesData(
            leftTitles: AxisTitles(sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 32,
              interval: maxY > 0 ? (maxY / 4).ceilToDouble() : 1,
              getTitlesWidget: (v, _) => Text(v.toInt().toString(),
                  style: TextStyle(fontSize: 10, color: Colors.grey[500])),
            )),
            bottomTitles: AxisTitles(sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 28,
              interval: data.length > 6 ? 2 : 1,
              getTitlesWidget: (value, _) {
                final idx = value.toInt();
                if (idx < 0 || idx >= data.length) return const SizedBox();
                final month = data[idx]['month'] as String;
                // Show as "Jan" style
                final parts = month.split('-');
                if (parts.length < 2) return const SizedBox();
                final months = ['','Jan','Feb','Mar','Apr','May','Jun',
                    'Jul','Aug','Sep','Oct','Nov','Dec'];
                final mNum = int.tryParse(parts[1]) ?? 0;
                return Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(mNum > 0 && mNum <= 12 ? months[mNum] : month,
                      style: TextStyle(fontSize: 10, color: Colors.grey[500])),
                );
              },
            )),
            topTitles:   const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          ),
          lineBarsData: [
            LineChartBarData(
              spots: spots,
              isCurved: true,
              curveSmoothness: 0.3,
              color: AppTheme.primaryGreen,
              barWidth: 2.5,
              isStrokeCapRound: true,
              dotData: FlDotData(
                show: true,
                getDotPainter: (spot, _, __, ___) => FlDotCirclePainter(
                  radius: 4,
                  color: AppTheme.primaryGreen,
                  strokeWidth: 2,
                  strokeColor: Colors.white,
                ),
              ),
              belowBarData: BarAreaData(
                show: true,
                color: AppTheme.primaryGreen.withOpacity(0.08),
              ),
            ),
          ],
          lineTouchData: LineTouchData(
            touchTooltipData: LineTouchTooltipData(
              getTooltipItems: (spots) => spots.map((s) => LineTooltipItem(
                '${s.y.toInt()} upload${s.y != 1 ? "s" : ""}',
                const TextStyle(color: Colors.white,
                    fontSize: 12, fontWeight: FontWeight.w600),
              )).toList(),
            ),
          ),
        ),
      ),
    );
  }

  // ── Recent uploads list ───────────────────────────────────
  Widget _buildRecentList(List<Map<String, dynamic>> data) {
    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: data.length,
      separatorBuilder: (_, __) => Divider(height: 1, color: Colors.grey.shade100),
      itemBuilder: (_, i) {
        final r      = data[i];
        final status = r['status'] as String;
        final color  = status == 'Approved'
            ? AppTheme.successGreen
            : status == 'Rejected'
                ? AppTheme.errorRed
                : AppTheme.gold;
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Row(children: [
            Container(
              width: 36, height: 36,
              decoration: BoxDecoration(
                color: AppTheme.lightGreen,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.description_outlined,
                  size: 18, color: AppTheme.primaryGreen),
            ),
            const SizedBox(width: 10),
            Expanded(child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(r['id'] as String,
                    style: const TextStyle(
                        fontWeight: FontWeight.w600, fontSize: 12)),
                Text('${r['type']}  •  ${r['user']}',
                    style: TextStyle(fontSize: 11, color: Colors.grey[500])),
              ],
            )),
            Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: color.withOpacity(0.3)),
                ),
                child: Text(status,
                    style: TextStyle(fontSize: 10, color: color,
                        fontWeight: FontWeight.w700)),
              ),
              const SizedBox(height: 2),
              Text(r['date'] as String,
                  style: TextStyle(fontSize: 10, color: Colors.grey[400])),
            ]),
          ]),
        );
      },
    );
  }

  Widget _emptyChart() => Center(
    child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
      Icon(Icons.bar_chart_outlined, size: 40, color: Colors.grey[300]),
      const SizedBox(height: 8),
      Text('No data yet', style: TextStyle(color: Colors.grey[400], fontSize: 13)),
    ]),
  );
}

// ── Stat card widget ──────────────────────────────────────────
class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10, offset: const Offset(0, 2))],
        ),
        child: Row(children: [
          Container(
            width: 48, height: 48,
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(width: 14),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(value,
                style: TextStyle(
                    fontSize: 28, fontWeight: FontWeight.w800, color: color,
                    height: 1.1)),
            Text(label,
                style: TextStyle(fontSize: 12, color: Colors.grey[500],
                    fontWeight: FontWeight.w500)),
          ]),
        ]),
      ),
    );
  }
}

// ── Chart card container ──────────────────────────────────────
class _ChartCard extends StatelessWidget {
  final String title;
  final Widget child;
  final double? height;

  const _ChartCard({
    required this.title,
    required this.child,
    this.height,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height ?? 300,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10, offset: const Offset(0, 2))],
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title,
            style: const TextStyle(
                fontSize: 13, fontWeight: FontWeight.w700,
                color: AppTheme.navy)),
        const SizedBox(height: 4),
        Divider(color: Colors.grey.shade100),
        const SizedBox(height: 4),
        Expanded(child: child),
      ]),
    );
  }
}
