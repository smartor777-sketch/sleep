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
  ) async {
    final hit = _hitTest(
      tapPosition: details.localPosition,
      size: size,
      nodes: nodes,
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
          await widget.onOpenDream(detail.dreamId);
        },
      ),
    );
  }

  DreamMapNode? _hitTest({
    required Offset tapPosition,
    required Size size,
    required List<DreamMapNode> nodes,
  }) {
    final base = math.min(size.width, size.height) * 0.78;
    final tile = base * _zoom;
    final origin =
        Offset((size.width - tile) / 2, (size.height - tile) / 2) + _pan;

    DreamMapNode? best;
    double bestDistance = 24;
    for (final node in nodes) {
      final radius = _nodeRadius(node);
      for (final dx in const [-1.0, 0.0, 1.0]) {
        for (final dy in const [-1.0, 0.0, 1.0]) {
          final point = Offset(
            origin.dx + (node.x + dx) * tile,
            origin.dy + (node.y + dy) * tile,
          );
          final distance = (point - tapPosition).distance;
          final hitRadius = math.max(18, radius + 10);
          if (distance <= hitRadius && distance < bestDistance) {
            best = node;
            bestDistance = distance;
          }
        }
      }
    }
    return best;
  }

  double _nodeRadius(DreamMapNode node) => 4 + (node.sizeWeight * 8);

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
        if (map == null || map.meta.totalNodes < map.meta.minChunksRequired) {
          final current = map?.meta.totalNodes ?? 0;
          final missing = math.max(
            0,
            (map?.meta.minChunksRequired ?? 5) - current,
          );
          return _MapEmptyState(missingCount: missing);
        }

        final visibleNodes = provider.visibleNodes;
        final clusters = map.clusters;

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
                    onPressed: () => provider.load(forceRefresh: true),
                    child: const Text('Refresh'),
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
                      selected: provider.selectedCluster == null,
                      onSelected: (_) => provider.setClusterFilter(null),
                    ),
                  ),
                  ...clusters.map(
                    (cluster) => Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(cluster.label),
                        selected: provider.selectedCluster == cluster.label,
                        onSelected: (_) => provider.setClusterFilter(
                          provider.selectedCluster == cluster.label
                              ? null
                              : cluster.label,
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
                  return GestureDetector(
                    onScaleStart: _handleScaleStart,
                    onScaleUpdate: _handleScaleUpdate,
                    onScaleEnd: _handleScaleEnd,
                    onTapUp: (details) =>
                        _handleTapUp(details, size, visibleNodes),
                    child: CustomPaint(
                      painter: _DreamMapPainter(
                        nodes: visibleNodes,
                        clusters: clusters,
                        pan: _pan,
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
    const repeats = [-1.0, 0.0, 1.0];
    for (final dx in repeats) {
      for (final dy in repeats) {
        final rect = Rect.fromLTWH(
          origin.dx + dx * tile,
          origin.dy + dy * tile,
          tile,
          tile,
        );
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
      }
    }
  }

  void _paintClusterHalos(Canvas canvas, Offset origin, double tile) {
    for (final cluster in clusters) {
      final baseColor = _parseHexColor(cluster.color) ?? accentColor;
      final haloPaint = Paint()
        ..color = baseColor.withOpacity(0.07)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 28);
      for (final dx in const [-1.0, 0.0, 1.0]) {
        for (final dy in const [-1.0, 0.0, 1.0]) {
          final center = Offset(
            origin.dx + (cluster.x + dx) * tile,
            origin.dy + (cluster.y + dy) * tile,
          );
          canvas.drawCircle(center, 44 * zoom.clamp(0.8, 1.5), haloPaint);
        }
      }
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

      for (final dx in const [-1.0, 0.0, 1.0]) {
        for (final dy in const [-1.0, 0.0, 1.0]) {
          final point = Offset(
            origin.dx + (node.x + dx) * tile,
            origin.dy + (node.y + dy) * tile,
          );
          canvas.drawCircle(point, radius + 2, glowPaint);
          canvas.drawCircle(point, radius, paint);
        }
      }
    }
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

  final DreamMapChunkDetail detail;
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
              detail.clusterLabel,
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(color: accentColor),
            ),
            const SizedBox(height: 6),
            Text(
              _formatDate(detail.date),
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 14),
            Text(detail.text),
            if (detail.neighbors.isNotEmpty) ...[
              const SizedBox(height: 16),
              Text(
                'Ближайшие чанки',
                style: Theme.of(context).textTheme.titleSmall,
              ),
              const SizedBox(height: 8),
              ...detail.neighbors
                  .take(3)
                  .map(
                    (neighbor) => Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Text(
                        '• ${neighbor.textPreview}',
                        style: Theme.of(context).textTheme.bodySmall,
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
                child: const Text('Открыть сон'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
