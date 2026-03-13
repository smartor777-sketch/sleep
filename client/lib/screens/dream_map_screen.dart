import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/dream_map.dart';
import '../providers/dream_map_provider.dart';
import '../utils/snackbar.dart';

class DreamMapScreen extends StatefulWidget {
  const DreamMapScreen({
    super.key,
    required this.accentColor,
    required this.onOpenDream,
  });

  final Color accentColor;
  final Future<void> Function(String dreamId) onOpenDream;

  @override
  State<DreamMapScreen> createState() => _DreamMapScreenState();
}

class _DreamMapScreenState extends State<DreamMapScreen> {
  Offset _pan = Offset.zero;
  double _zoom = 1.0;
  Offset? _lastFocalPoint;
  double? _scaleAtStart;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DreamMapProvider>().load();
    });
  }

  void _resetView() {
    setState(() {
      _pan = Offset.zero;
      _zoom = 1.0;
      _lastFocalPoint = null;
      _scaleAtStart = null;
    });
  }

  void _handleScaleStart(ScaleStartDetails details) {
    _lastFocalPoint = details.focalPoint;
    _scaleAtStart = _zoom;
  }

  void _handleScaleUpdate(ScaleUpdateDetails details) {
    final previous = _lastFocalPoint;
    if (previous == null) {
      _lastFocalPoint = details.focalPoint;
      return;
    }

    setState(() {
      if (details.scale != 1.0 && _scaleAtStart != null) {
        _zoom = (_scaleAtStart! * details.scale).clamp(0.7, 3.0);
      }
      final delta = details.focalPoint - previous;
      _pan += delta;
      _lastFocalPoint = details.focalPoint;
    });
  }

  void _handleScaleEnd(ScaleEndDetails details) {
    _lastFocalPoint = null;
    _scaleAtStart = null;
  }

  Future<void> _handleTapUp(
    TapUpDetails details,
    Size size,
    List<DreamMapNode> nodes,
    Offset clampedPan,
  ) async {
    final hit = _hitTest(
      tapPosition: details.localPosition,
      size: size,
      nodes: nodes,
      pan: clampedPan,
    );
    if (hit == null) {
      context.read<DreamMapProvider>().clearSelection();
      return;
    }
    await context.read<DreamMapProvider>().selectNode(hit.id);
    if (!mounted) return;
    final detail = context.read<DreamMapProvider>().selectedDetail;
    if (detail == null) return;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) => _MapDetailSheet(
        detail: detail,
        accentColor: widget.accentColor,
        onOpenDream: () async {
          Navigator.of(context).pop();
          await widget.onOpenDream(detail.primaryDreamId);
        },
      ),
    );
  }

  DreamMapNode? _hitTest({
    required Offset tapPosition,
    required Size size,
    required List<DreamMapNode> nodes,
    required Offset pan,
  }) {
    final base = math.min(size.width, size.height) * 0.78;
    final tile = base * _zoom;
    final origin = _mapOrigin(size, tile, pan);

    DreamMapNode? best;
    double bestDistance = 24;
    for (final node in nodes) {
      final radius = _nodeRadius(node);
      final point = Offset(
        origin.dx + node.x * tile,
        origin.dy + node.y * tile,
      );
      final distance = (point - tapPosition).distance;
      final hitRadius = math.max(18, radius + 10);
      if (distance <= hitRadius && distance < bestDistance) {
        best = node;
        bestDistance = distance;
      }
    }
    return best;
  }

  double _nodeRadius(DreamMapNode node) => 4 + (node.sizeWeight * 8);

  Offset _mapOrigin(Size size, double tile, Offset pan) {
    return Offset((size.width - tile) / 2, (size.height - tile) / 2) + pan;
  }

  Offset _clampPan(Offset pan, Size size, double tile) {
    final limitX = math.max(0.0, (tile - size.width) / 2 + 28);
    final limitY = math.max(0.0, (tile - size.height) / 2 + 28);
    return Offset(
      pan.dx.clamp(-limitX, limitX).toDouble(),
      pan.dy.clamp(-limitY, limitY).toDouble(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<DreamMapProvider>(
      builder: (context, provider, _) {
        if (provider.error != null) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            showToast(context, provider.error!, isError: true);
            provider.clearError();
          });
        }

        final map = provider.map;
        if (provider.loading && map == null) {
          return const Center(child: CircularProgressIndicator());
        }
        if (map == null || map.meta.totalNodes < map.meta.minNodesRequired) {
          final current = map?.meta.totalNodes ?? 0;
          final missing = math.max(
            0,
            (map?.meta.minNodesRequired ?? 5) - current,
          );
          return _MapEmptyState(missingCount: missing);
        }

        final visibleNodes = provider.visibleNodes;
        final clusters = map.clusters;
        final archetypeFilters = map.archetypeFilters;

        return Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
              child: Row(
                children: [
                  Text(
                    'Dream Map',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const Spacer(),
                  TextButton(onPressed: _resetView, child: const Text('Reset')),
                  TextButton(
                    onPressed: provider.refreshing
                        ? null
                        : () => provider.load(forceRefresh: true),
                    child: const Text('Обновить'),
                  ),
                ],
              ),
            ),
            SizedBox(
              height: 42,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                children: [
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: const Text('All'),
                      selected: provider.selectedArchetype == null,
                      onSelected: (_) => provider.setArchetypeFilter(null),
                    ),
                  ),
                  ...archetypeFilters.map(
                    (archetype) => Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(archetype),
                        selected: provider.selectedArchetype == archetype,
                        onSelected: (_) => provider.setArchetypeFilter(
                          provider.selectedArchetype == archetype
                              ? null
                              : archetype,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 10, 16, 8),
              child: Row(
                children: [
                  _MapHudPill(label: '${visibleNodes.length} nodes'),
                  const SizedBox(width: 8),
                  _MapHudPill(label: 'zoom ${_zoom.toStringAsFixed(2)}x'),
                  const SizedBox(width: 8),
                  _MapHudPill(label: map.meta.cached ? 'cached' : 'live'),
                  if (provider.refreshing) ...[
                    const SizedBox(width: 8),
                    const Expanded(
                      child: _MapHudPill(
                        label:
                            'Карта обновляется. Пока показываем предыдущую версию.',
                      ),
                    ),
                  ],
                ],
              ),
            ),
            Expanded(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final size = Size(
                    constraints.maxWidth,
                    constraints.maxHeight,
                  );
                  final tile =
                      math.min(size.width, size.height) * 0.78 * _zoom;
                  final clampedPan = _clampPan(_pan, size, tile);
                  return GestureDetector(
                    onScaleStart: _handleScaleStart,
                    onScaleUpdate: _handleScaleUpdate,
                    onScaleEnd: _handleScaleEnd,
                    onTapUp: (details) =>
                        _handleTapUp(details, size, visibleNodes, clampedPan),
                    child: CustomPaint(
                      painter: _DreamMapPainter(
                        nodes: visibleNodes,
                        clusters: clusters,
                        pan: clampedPan,
                        zoom: _zoom,
                        accentColor: widget.accentColor,
                        brightness: Theme.of(context).brightness,
                      ),
                      child: const SizedBox.expand(),
                    ),
                  );
                },
              ),
            ),
          ],
        );
      },
    );
  }
}

class _DreamMapPainter extends CustomPainter {
  const _DreamMapPainter({
    required this.nodes,
    required this.clusters,
    required this.pan,
    required this.zoom,
    required this.accentColor,
    required this.brightness,
  });

  final List<DreamMapNode> nodes;
  final List<DreamMapCluster> clusters;
  final Offset pan;
  final double zoom;
  final Color accentColor;
  final Brightness brightness;

  @override
  void paint(Canvas canvas, Size size) {
    final base = math.min(size.width, size.height) * 0.78;
    final tile = base * zoom;
    final origin =
        Offset((size.width - tile) / 2, (size.height - tile) / 2) + pan;

    _paintBackground(canvas, size, origin, tile);
    _paintClusterHalos(canvas, origin, tile);
    _paintNodes(canvas, origin, tile);
    _paintLabels(canvas, size, origin, tile);
  }

  void _paintBackground(Canvas canvas, Size size, Offset origin, double tile) {
    final background = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: brightness == Brightness.dark
            ? [
                const Color(0xFF0F1115),
                const Color(0xFF151923),
                const Color(0xFF0D111A),
              ]
            : [
                const Color(0xFFF8F6F0),
                const Color(0xFFF1F4FB),
                const Color(0xFFF8F8FC),
              ],
      ).createShader(Offset.zero & size);
    canvas.drawRect(Offset.zero & size, background);

    final gridPaint = Paint()
      ..color = (brightness == Brightness.dark ? Colors.white : Colors.black)
          .withOpacity(0.06)
      ..strokeWidth = 1;
    final rect = Rect.fromLTWH(origin.dx, origin.dy, tile, tile);
    for (var i = 0; i <= 8; i++) {
      final t = i / 8;
      canvas.drawLine(
        Offset(rect.left + t * rect.width, rect.top),
        Offset(rect.left + t * rect.width, rect.bottom),
        gridPaint,
      );
      canvas.drawLine(
        Offset(rect.left, rect.top + t * rect.height),
        Offset(rect.right, rect.top + t * rect.height),
        gridPaint,
      );
    }
    final borderPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2
      ..color = (brightness == Brightness.dark ? Colors.white : Colors.black)
          .withOpacity(0.18);
    canvas.drawRect(rect, borderPaint);
  }

  void _paintClusterHalos(Canvas canvas, Offset origin, double tile) {
    for (final cluster in clusters) {
      final baseColor = _parseHexColor(cluster.color) ?? accentColor;
      final haloPaint = Paint()
        ..color = baseColor.withOpacity(0.07)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 28);
      final center = Offset(
        origin.dx + cluster.x * tile,
        origin.dy + cluster.y * tile,
      );
      canvas.drawCircle(center, 44 * zoom.clamp(0.8, 1.5), haloPaint);
    }
  }

  void _paintNodes(Canvas canvas, Offset origin, double tile) {
    final neutral = brightness == Brightness.dark
        ? Colors.white.withOpacity(0.18)
        : Colors.black.withOpacity(0.16);
    for (final node in nodes) {
      final mixed =
          Color.lerp(
            neutral,
            accentColor,
            ((node.z + 1) / 2).clamp(0.0, 1.0),
          ) ??
          accentColor;
      final paint = Paint()..color = mixed;
      final glowPaint = Paint()
        ..color = mixed.withOpacity(0.22)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 12);
      final radius = 4 + (node.sizeWeight * 8);

      final point = Offset(
        origin.dx + node.x * tile,
        origin.dy + node.y * tile,
      );
      canvas.drawCircle(point, radius + 2, glowPaint);
      canvas.drawCircle(point, radius, paint);
    }
  }

  void _paintLabels(Canvas canvas, Size size, Offset origin, double tile) {
    if (zoom < 1.05) return;

    final visibleBounds = Offset.zero & size;
    final neutralText = brightness == Brightness.dark
        ? Colors.white
        : const Color(0xFF12161F);
    final backgroundBase = brightness == Brightness.dark
        ? const Color(0xFF10141D)
        : Colors.white;
    final cellSize = zoom >= 1.9
        ? 72.0
        : zoom >= 1.45
        ? 88.0
        : 108.0;
    final occupiedCells = <String>{};

    final sortedNodes = [...nodes]
      ..sort((a, b) {
        final aScore = (a.sizeWeight * 0.65) + (a.cosineSimToCenter * 0.35);
        final bScore = (b.sizeWeight * 0.65) + (b.cosineSimToCenter * 0.35);
        return bScore.compareTo(aScore);
      });

    for (final node in sortedNodes) {
      final label = _labelForNode(node);
      if (label.isEmpty) continue;

      final point = Offset(
        origin.dx + node.x * tile,
        origin.dy + node.y * tile,
      );
      if (!visibleBounds.inflate(48).contains(point)) continue;

      final cellKey =
          '${(point.dx / cellSize).floor()}:${(point.dy / cellSize).floor()}';
      if (occupiedCells.contains(cellKey)) continue;

      final textPainter = TextPainter(
        text: TextSpan(
          text: label,
          style: TextStyle(
            color: neutralText,
            fontSize: zoom >= 1.9 ? 12 : 11,
            fontWeight: FontWeight.w500,
            height: 1.15,
          ),
        ),
        maxLines: 2,
        ellipsis: '…',
        textDirection: TextDirection.ltr,
      )..layout(maxWidth: zoom >= 1.9 ? 110 : 92);

      final padding = const EdgeInsets.symmetric(
        horizontal: 8,
        vertical: 5,
      );
      final labelSize = Size(
        textPainter.width + padding.horizontal,
        textPainter.height + padding.vertical,
      );
      var topLeft = Offset(
        point.dx - (labelSize.width / 2),
        point.dy - 18 - labelSize.height,
      );
      if (topLeft.dx < 8) topLeft = Offset(8, topLeft.dy);
      if (topLeft.dx + labelSize.width > size.width - 8) {
        topLeft = Offset(size.width - 8 - labelSize.width, topLeft.dy);
      }
      if (topLeft.dy < 8) {
        topLeft = Offset(topLeft.dx, point.dy + 14);
      }

      final rect = RRect.fromRectAndRadius(
        topLeft & labelSize,
        const Radius.circular(12),
      );
      final fill = Paint()
        ..color = backgroundBase.withOpacity(
          brightness == Brightness.dark ? 0.78 : 0.86,
        );
      final stroke = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1
        ..color = accentColor.withOpacity(0.18);
      canvas.drawRRect(rect, fill);
      canvas.drawRRect(rect, stroke);
      textPainter.paint(
        canvas,
        topLeft + Offset(padding.left, padding.top - 0.5),
      );
      occupiedCells.add(cellKey);
    }
  }

  String _labelForNode(DreamMapNode node) {
    return node.displayLabel.trim().isEmpty
        ? node.symbolName
        : node.displayLabel.trim();
  }

  Color? _parseHexColor(String? value) {
    final raw = value?.trim();
    if (raw == null || !RegExp(r'^#[0-9A-Fa-f]{6}$').hasMatch(raw)) return null;
    return Color(int.parse('FF${raw.substring(1)}', radix: 16));
  }

  @override
  bool shouldRepaint(covariant _DreamMapPainter oldDelegate) {
    return oldDelegate.nodes != nodes ||
        oldDelegate.clusters != clusters ||
        oldDelegate.pan != pan ||
        oldDelegate.zoom != zoom ||
        oldDelegate.accentColor != accentColor ||
        oldDelegate.brightness != brightness;
  }
}

class _MapHudPill extends StatelessWidget {
  const _MapHudPill({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: Theme.of(
          context,
        ).colorScheme.surfaceContainerHighest.withOpacity(0.6),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(label, style: Theme.of(context).textTheme.bodySmall),
    );
  }
}

class _MapEmptyState extends StatelessWidget {
  const _MapEmptyState({required this.missingCount});

  final int missingCount;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 28),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Dream Map', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 10),
            Text(
              missingCount > 0
                  ? 'Добавьте ещё $missingCount снов, чтобы активировать карту.'
                  : 'Карта пока недоступна.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MapDetailSheet extends StatelessWidget {
  const _MapDetailSheet({
    required this.detail,
    required this.accentColor,
    required this.onOpenDream,
  });

  final DreamMapSymbolDetail detail;
  final Color accentColor;
  final Future<void> Function() onOpenDream;

  String _formatDate(DateTime date) {
    final day = date.day.toString().padLeft(2, '0');
    final month = date.month.toString().padLeft(2, '0');
    final year = date.year.toString();
    return '$day.$month.$year';
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 18),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 44,
              height: 4,
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.outline.withOpacity(0.3),
                borderRadius: BorderRadius.circular(999),
              ),
            ),
            Text(
              detail.displayLabel,
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(color: accentColor),
            ),
            const SizedBox(height: 6),
            Text(
              'Символ: ${detail.symbolName}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 4),
            Text(
              'Последнее появление: ${_formatDate(detail.lastSeenAt)}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 14),
            Text(
              '${detail.occurrenceCount} вхождений в ${detail.dreamCount} снах',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            if (detail.relatedArchetypes.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text('Архетипы', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: detail.relatedArchetypes
                    .map(
                      (item) => Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: accentColor.withOpacity(0.12),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          item,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ),
                    )
                    .toList(),
              ),
            ],
            if (detail.relatedSymbols.isNotEmpty) ...[
              const SizedBox(height: 16),
              Text(
                'Связанные символы',
                style: Theme.of(context).textTheme.titleSmall,
              ),
              const SizedBox(height: 8),
              ...detail.relatedSymbols
                  .take(5)
                  .map(
                    (symbol) => Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Text(
                        '• $symbol',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                  ),
            ],
            if (detail.occurrences.isNotEmpty) ...[
              const SizedBox(height: 16),
              Text(
                'Где встречается',
                style: Theme.of(context).textTheme.titleSmall,
              ),
              const SizedBox(height: 8),
              ...detail.occurrences
                  .take(4)
                  .map(
                    (occurrence) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _formatDate(occurrence.date),
                            style: Theme.of(
                              context,
                            ).textTheme.bodySmall?.copyWith(color: accentColor),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            occurrence.textPreview,
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                  ),
            ],
            const SizedBox(height: 18),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: accentColor,
                  foregroundColor: Colors.white,
                ),
                onPressed: onOpenDream,
                child: const Text('Открыть последний сон'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
