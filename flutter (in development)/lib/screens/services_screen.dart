import 'package:flutter/material.dart';
import '../theme.dart';
import 'certifications_screen.dart';
import 'marriage_license_screen.dart';

class ServicesScreen extends StatelessWidget {
  const ServicesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text(
            'SERVICES',
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.w800,
              color: AppTheme.navy,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 40),
          _ServiceButton(
            label: 'CERTIFICATIONS',
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const CertificationsScreen()),
            ),
          ),
          const SizedBox(height: 16),
          _ServiceButton(
            label: 'APPLICATION FOR\nMARRIAGE LICENSE',
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const MarriageLicenseScreen()),
            ),
          ),
        ],
      ),
    );
  }
}

class _ServiceButton extends StatefulWidget {
  final String label;
  final VoidCallback onTap;

  const _ServiceButton({required this.label, required this.onTap});

  @override
  State<_ServiceButton> createState() => _ServiceButtonState();
}

class _ServiceButtonState extends State<_ServiceButton> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit:  (_) => setState(() => _hovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          width: 420,
          padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 24),
          decoration: BoxDecoration(
            color: _hovered ? AppTheme.lightGreen : Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: AppTheme.primaryGreen,
              width: 2,
            ),
            boxShadow: _hovered
                ? [BoxShadow(color: AppTheme.primaryGreen.withOpacity(0.15), blurRadius: 12, offset: const Offset(0, 4))]
                : [],
          ),
          child: Text(
            widget.label,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: _hovered ? AppTheme.darkGreen : AppTheme.navy,
              letterSpacing: 1.2,
              height: 1.5,
            ),
          ),
        ),
      ),
    );
  }
}