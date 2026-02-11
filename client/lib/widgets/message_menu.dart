import 'dart:ui';

import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';

class MessageMenu {
  static Future<void> show(
    BuildContext context, {
    required Offset position,
    required VoidCallback onCopy,
    required VoidCallback onEdit,
    required VoidCallback onDelete,
    required VoidCallback onAnalyze,
  }) async {
    final size = MediaQuery.of(context).size;
    const menuWidth = 220.0;
    const menuHeight = 220.0;

    final double left = (position.dx - menuWidth / 2)
        .clamp(16.0, size.width - menuWidth - 16);
    final double top = (position.dy - menuHeight)
        .clamp(16.0, size.height - menuHeight - 16);

    final selected = await showGeneralDialog<int>(
      context: context,
      barrierDismissible: true,
      barrierLabel: 'Message menu',
      barrierColor: Colors.transparent,
      pageBuilder: (dialogContext, animation, secondaryAnimation) {
        return Material(
          color: Colors.transparent,
          child: Stack(
            children: [
              Positioned.fill(
                child: GestureDetector(
                  onTap: () => Navigator.of(dialogContext).pop(),
                  child: BackdropFilter(
                    filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
                    child: Container(
                      color: Colors.black.withOpacity(0.2),
                    ),
                  ),
                ),
              ),
              Positioned(
                left: left,
                top: top,
                child: _MenuCard(
                  onSelected: (value) =>
                      Navigator.of(dialogContext).pop(value),
                ),
              ),
            ],
          ),
        );
      },
    );

    switch (selected) {
      case 0:
        onCopy();
        break;
      case 1:
        onEdit();
        break;
      case 2:
        onDelete();
        break;
      case 3:
        onAnalyze();
        break;
    }
  }
}

class _MenuCard extends StatelessWidget {
  final ValueChanged<int> onSelected;

  const _MenuCard({required this.onSelected});

  @override
  Widget build(BuildContext context) {
    final surface = Theme.of(context).colorScheme.surface;
    final onSurface = Theme.of(context).colorScheme.onSurface;

    final l10n = AppLocalizations.of(context)!;
    final items = [
      _MenuItemData(0, l10n.copy, Icons.copy),
      _MenuItemData(1, l10n.edit, Icons.edit),
      _MenuItemData(2, l10n.delete, Icons.delete_outline),
      _MenuItemData(3, l10n.analyze, Icons.analytics_outlined),
    ];

    return Card(
      elevation: 8,
      color: surface,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ConstrainedBox(
        constraints: const BoxConstraints(minWidth: 200, maxWidth: 240),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: items
                .map(
                  (item) => ListTile(
                    dense: true,
                    leading: Icon(item.icon, color: onSurface),
                    title: Text(item.label),
                    onTap: () => onSelected(item.value),
                  ),
                )
                .toList(),
          ),
        ),
      ),
    );
  }
}

class _MenuItemData {
  final int value;
  final String label;
  final IconData icon;

  const _MenuItemData(this.value, this.label, this.icon);
}