class DreamMapNode {
  final String id;
  final String symbolName;
  final String displayLabel;
  final double x;
  final double y;
  final double z;
  final int clusterId;
  final String clusterLabel;
  final String archetypeColor;
  final double cosineSimToCenter;
  final double sizeWeight;
  final int occurrenceCount;
  final int dreamCount;
  final DateTime lastSeenAt;
  final String previewText;
  final List<String> relatedArchetypes;

  DreamMapNode({
    required this.id,
    required this.symbolName,
    required this.displayLabel,
    required this.x,
    required this.y,
    required this.z,
    required this.clusterId,
    required this.clusterLabel,
    required this.archetypeColor,
    required this.cosineSimToCenter,
    required this.sizeWeight,
    required this.occurrenceCount,
    required this.dreamCount,
    required this.lastSeenAt,
    required this.previewText,
    required this.relatedArchetypes,
  });

  factory DreamMapNode.fromJson(Map<String, dynamic> json) {
    return DreamMapNode(
      id: json['id'] as String,
      symbolName: json['symbol_name'] as String? ?? '',
      displayLabel: json['display_label'] as String? ?? '',
      x: (json['x'] as num).toDouble(),
      y: (json['y'] as num).toDouble(),
      z: (json['z'] as num).toDouble(),
      clusterId: json['cluster_id'] as int,
      clusterLabel: json['cluster_label'] as String? ?? 'Unknown',
      archetypeColor: json['archetype_color'] as String? ?? '#98A2B3',
      cosineSimToCenter:
          (json['cosine_sim_to_center'] as num?)?.toDouble() ?? 0.0,
      sizeWeight: (json['size_weight'] as num?)?.toDouble() ?? 0.0,
      occurrenceCount: json['occurrence_count'] as int? ?? 1,
      dreamCount: json['dream_count'] as int? ?? 1,
      lastSeenAt: DateTime.parse(json['last_seen_at'] as String),
      previewText: json['preview_text'] as String? ?? '',
      relatedArchetypes:
          (json['related_archetypes'] as List<dynamic>? ?? const [])
              .map((item) => item.toString())
              .toList(),
    );
  }
}

class DreamMapCluster {
  final int id;
  final String label;
  final String color;
  final int count;
  final double x;
  final double y;

  DreamMapCluster({
    required this.id,
    required this.label,
    required this.color,
    required this.count,
    required this.x,
    required this.y,
  });

  factory DreamMapCluster.fromJson(Map<String, dynamic> json) {
    final center = json['center'] as Map<String, dynamic>? ?? const {};
    return DreamMapCluster(
      id: json['id'] as int,
      label: json['label'] as String? ?? 'Unknown',
      color: json['color'] as String? ?? '#98A2B3',
      count: json['count'] as int? ?? 0,
      x: (center['x'] as num?)?.toDouble() ?? 0.0,
      y: (center['y'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class DreamMapMeta {
  final int totalNodes;
  final int totalClusters;
  final bool cached;
  final String computedWith;
  final String clusterMethod;
  final int minNodesRequired;

  DreamMapMeta({
    required this.totalNodes,
    required this.totalClusters,
    required this.cached,
    required this.computedWith,
    required this.clusterMethod,
    required this.minNodesRequired,
  });

  factory DreamMapMeta.fromJson(Map<String, dynamic> json) {
    return DreamMapMeta(
      totalNodes: json['total_nodes'] as int? ?? 0,
      totalClusters: json['total_clusters'] as int? ?? 0,
      cached: json['cached'] as bool? ?? false,
      computedWith: json['computed_with'] as String? ?? 'unknown',
      clusterMethod: json['cluster_method'] as String? ?? 'unknown',
      minNodesRequired: json['min_nodes_required'] as int? ?? 5,
    );
  }
}

class DreamMapData {
  final List<DreamMapNode> nodes;
  final List<DreamMapCluster> clusters;
  final List<String> archetypeFilters;
  final DreamMapMeta meta;

  DreamMapData({
    required this.nodes,
    required this.clusters,
    required this.archetypeFilters,
    required this.meta,
  });

  factory DreamMapData.fromJson(Map<String, dynamic> json) {
    final nodesJson = json['nodes'] as List<dynamic>? ?? const [];
    final clustersJson = json['clusters'] as List<dynamic>? ?? const [];
    final archetypesJson =
        json['archetype_filters'] as List<dynamic>? ?? const [];
    return DreamMapData(
      nodes: nodesJson
          .map((item) => DreamMapNode.fromJson(item as Map<String, dynamic>))
          .toList(),
      clusters: clustersJson
          .map((item) => DreamMapCluster.fromJson(item as Map<String, dynamic>))
          .toList(),
      archetypeFilters: archetypesJson.map((item) => item.toString()).toList(),
      meta: DreamMapMeta.fromJson(
        json['meta'] as Map<String, dynamic>? ?? const {},
      ),
    );
  }
}

class DreamMapOccurrence {
  final String dreamId;
  final DateTime date;
  final String textPreview;

  DreamMapOccurrence({
    required this.dreamId,
    required this.date,
    required this.textPreview,
  });

  factory DreamMapOccurrence.fromJson(Map<String, dynamic> json) {
    return DreamMapOccurrence(
      dreamId: json['dream_id'] as String,
      date: DateTime.parse(json['date'] as String),
      textPreview: json['text_preview'] as String? ?? '',
    );
  }
}

class DreamMapSymbolDetail {
  final String id;
  final String symbolName;
  final String displayLabel;
  final String primaryDreamId;
  final int clusterId;
  final String clusterLabel;
  final String archetypeColor;
  final int occurrenceCount;
  final int dreamCount;
  final double z;
  final double sizeWeight;
  final DateTime lastSeenAt;
  final List<String> relatedArchetypes;
  final List<String> relatedSymbols;
  final List<DreamMapOccurrence> occurrences;

  DreamMapSymbolDetail({
    required this.id,
    required this.symbolName,
    required this.displayLabel,
    required this.primaryDreamId,
    required this.clusterId,
    required this.clusterLabel,
    required this.archetypeColor,
    required this.occurrenceCount,
    required this.dreamCount,
    required this.z,
    required this.sizeWeight,
    required this.lastSeenAt,
    required this.relatedArchetypes,
    required this.relatedSymbols,
    required this.occurrences,
  });

  factory DreamMapSymbolDetail.fromJson(Map<String, dynamic> json) {
    final occurrencesJson = json['occurrences'] as List<dynamic>? ?? const [];
    final rawArchetypes =
        json['related_archetypes'] as List<dynamic>? ?? const [];
    final rawSymbols = json['related_symbols'] as List<dynamic>? ?? const [];
    return DreamMapSymbolDetail(
      id: json['id'] as String,
      symbolName: json['symbol_name'] as String? ?? '',
      displayLabel: json['display_label'] as String? ?? '',
      primaryDreamId: json['primary_dream_id'] as String? ?? '',
      clusterId: json['cluster_id'] as int,
      clusterLabel: json['cluster_label'] as String? ?? 'Unknown',
      archetypeColor: json['archetype_color'] as String? ?? '#98A2B3',
      occurrenceCount: json['occurrence_count'] as int? ?? 1,
      dreamCount: json['dream_count'] as int? ?? 1,
      z: (json['z'] as num?)?.toDouble() ?? 0.0,
      sizeWeight: (json['size_weight'] as num?)?.toDouble() ?? 0.0,
      lastSeenAt: DateTime.parse(json['last_seen_at'] as String),
      relatedArchetypes: rawArchetypes.map((item) => item.toString()).toList(),
      relatedSymbols: rawSymbols.map((item) => item.toString()).toList(),
      occurrences: occurrencesJson
          .map(
            (item) => DreamMapOccurrence.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
    );
  }
}
