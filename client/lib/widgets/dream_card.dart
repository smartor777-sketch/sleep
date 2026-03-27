import 'package:flutter/material.dart';
import '../models/dream.dart';
import '../l10n/app_localizations.dart';

class DreamCard extends StatelessWidget {
  final Dream dream;
  final Color accentColor;
  final GestureLongPressStartCallback? onLongPressStart;
  final VoidCallback? onTap;
  final VoidCallback? onAnalyzeTap;

  const DreamCard({
    super.key,
    required this.dream,
    required this.accentColor,
    this.onLongPressStart,
    this.onTap,
    this.onAnalyzeTap,
  });

  String _formatDate(DateTime date) {
    final day = date.day.toString().padLeft(2, '0');
    final month = date.month.toString().padLeft(2, '0');
    final year = date.year;
    return '$day.$month.$year';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final background = theme.colorScheme.surface;
    final color1 = _parseHexColor(dream.gradientColor1) ?? const Color(0xFFFA9042);
    final color2 = _parseHexColor(dream.gradientColor2) ?? const Color(0xFF8885FF);
    final titleText = (dream.title?.trim().isNotEmpty ?? false)
        ? dream.title!.trim()
        : dream.content.trim();
    const textColor = Colors.white;
    final dateColor = Colors.white.withOpacity(0.68);

    return GestureDetector(
      onLongPressStart: onLongPressStart,
      onTap: onTap,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14),
        child: Container(
          width: double.infinity,
          height: double.infinity,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              stops: const [0.0, 0.52, 1.0],
              colors: [color1, color2, background],
            ),
          ),
          child: Stack(
            fit: StackFit.expand,
            children: [
              DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.black.withOpacity(0.12),
                      Colors.transparent,
                      Colors.black.withOpacity(0.28),
                    ],
                    stops: const [0.0, 0.42, 1.0],
                  ),
                ),
              ),
              if (dream.analysisStatus == 'analyzing')
                Container(
                  color: Colors.black.withOpacity(0.18),
                  child: const Center(
                    child: SizedBox(
                      width: 28,
                      height: 28,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.4,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
              if (dream.analysisStatus == 'analysis_failed')
                Align(
                  alignment: Alignment.topRight,
                  child: Padding(
                    padding: const EdgeInsets.all(8),
                    child: Container(
                      padding: const EdgeInsets.all(4),
                      decoration: BoxDecoration(
                        color: Colors.red.withOpacity(0.88),
                        borderRadius: BorderRadius.circular(999),
                      ),
                      child: const Icon(
                        Icons.error_outline,
                        size: 14,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
              if (dream.analysisStatus == 'saved' && onAnalyzeTap != null)
                Align(
                  alignment: Alignment.bottomCenter,
                  child: Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: GestureDetector(
                      onTap: onAnalyzeTap,
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.black.withOpacity(0.32),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          AppLocalizations.of(context)?.analyze ?? 'Analyze',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 11,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              Padding(
                padding: const EdgeInsets.fromLTRB(10, 9, 10, 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _formatDate(dream.createdAt),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: dateColor,
                        fontSize: 11,
                        shadows: const [
                          Shadow(
                            color: Color(0x55000000),
                            blurRadius: 6,
                            offset: Offset(0, 1),
                          ),
                        ],
                      ),
                    ),
                    const Spacer(),
                    Text(
                      titleText.length > 32
                          ? '${titleText.substring(0, 32)}...'
                          : titleText,
                      maxLines: 3,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.titleSmall?.copyWith(
                        color: textColor,
                        fontSize: 12,
                        fontWeight: FontWeight.w400,
                        height: 1.12,
                        shadows: const [
                          Shadow(
                            color: Color(0x70000000),
                            blurRadius: 10,
                            offset: Offset(0, 2),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color? _parseHexColor(String? value) {
    final raw = value?.trim();
    if (raw == null || !RegExp(r'^#[0-9A-Fa-f]{6}$').hasMatch(raw)) return null;
    final hex = raw.substring(1);
    return Color(int.parse('FF$hex', radix: 16));
  }
}
