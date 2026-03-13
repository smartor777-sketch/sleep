class DreamMapNode {
  final String id;
  final String dreamId;
  final double x;
  final double y;
  final double z;
  final int clusterId;
  final String clusterLabel;
  final String archetypeColor;
  final double cosineSimToCenter;
  final double sizeWeight;
  final String textPreview;
  final DateTime date;
  final double emotionValence;
  final int tokens;

  DreamMapNode({
    required this.id,
    required this.dreamId,
    required this.x,
    required this.y,
    required this.z,
    required this.clusterId,
    required this.clusterLabel,
    required this.archetypeColor,
    required this.cosineSimToCenter,
    required this.sizeWeight,
    required this.textPreview,
    required this.date,
    required this.emotionValence,
    required this.tokens,
  });

  factory DreamMapNode.fromJson(Map<String, dynamic> json) {
    return DreamMapNode(
      id: json['id'] as String,
      dreamId: json['dream_id'] as String,
      x: (json['x'] as num).toDouble(),
      y: (json['y'] as num).toDouble(),
      z: (json['z'] as num).toDouble(),
      clusterId: json['cluster_id'] as int,
      clusterLabel: json['cluster_label'] as String? ?? 'Unknown',
      archetypeColor: json['archetype_color'] as String? ?? '#98A2B3',
      cosineSimToCenter:
          (json['cosine_sim_to_center'] as num?)?.toDouble() ?? 0.0,
      sizeWeight: (json['size_weight'] as num?)?.toDouble() ?? 0.0,
      textPreview: json['text_preview'] as String? ?? '',
      date: DateTime.parse(json['date'] as String),
      emotionValence: (json['emotion_valence'] as num?)?.toDouble() ?? 0.0,
      tokens: json['tokens'] as int? ?? 0,
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
  final int minChunksRequired;

  DreamMapMeta({
    required this.totalNodes,
    required this.totalClusters,
    required this.cached,
    required this.computedWith,
    required this.clusterMethod,
    required this.minChunksRequired,
  });

  factory DreamMapMeta.fromJson(Map<String, dynamic> json) {
    return DreamMapMeta(
      totalNodes: json['total_nodes'] as int? ?? 0,
      totalClusters: json['total_clusters'] as int? ?? 0,
      cached: json['cached'] as bool? ?? false,
      computedWith: json['computed_with'] as String? ?? 'unknown',
      clusterMethod: json['cluster_method'] as String? ?? 'unknown',
      minChunksRequired: json['min_chunks_required'] as int? ?? 5,
    );
  }
}

class DreamMapData {
  final List<DreamMapNode> nodes;
  final List<DreamMapCluster> clusters;
  final DreamMapMeta meta;

  DreamMapData({
    required this.nodes,
    required this.clusters,
    required this.meta,
  });

  factory DreamMapData.fromJson(Map<String, dynamic> json) {
    final nodesJson = json['nodes'] as List<dynamic>? ?? const [];
    final clustersJson = json['clusters'] as List<dynamic>? ?? const [];
    return DreamMapData(
      nodes: nodesJson
          .map((item) => DreamMapNode.fromJson(item as Map<String, dynamic>))
          .toList(),
      clusters: clustersJson
          .map((item) => DreamMapCluster.fromJson(item as Map<String, dynamic>))
          .toList(),
      meta: DreamMapMeta.fromJson(
        json['meta'] as Map<String, dynamic>? ?? const {},
      ),
    );
  }
}

class DreamMapNeighbor {
  final String chunkId;
  final String dreamId;
  final String textPreview;
  final double cosineSimilarity;
  final DateTime date;

  DreamMapNeighbor({
    required this.chunkId,
    required this.dreamId,
    required this.textPreview,
    required this.cosineSimilarity,
    required this.date,
  });

  factory DreamMapNeighbor.fromJson(Map<String, dynamic> json) {
    return DreamMapNeighbor(
      chunkId: json['chunk_id'] as String,
      dreamId: json['dream_id'] as String,
      textPreview: json['text_preview'] as String? ?? '',
      cosineSimilarity: (json['cosine_similarity'] as num?)?.toDouble() ?? 0.0,
      date: DateTime.parse(json['date'] as String),
    );
  }
}

class DreamMapChunkDetail {
  final String id;
  final String dreamId;
  final int clusterId;
  final String clusterLabel;
  final String archetypeColor;
  final String text;
  final DateTime date;
  final double emotionValence;
  final int tokens;
  final double z;
  final double sizeWeight;
  final List<DreamMapNeighbor> neighbors;

  DreamMapChunkDetail({
    required this.id,
    required this.dreamId,
    required this.clusterId,
    required this.clusterLabel,
    required this.archetypeColor,
    required this.text,
    required this.date,
    required this.emotionValence,
    required this.tokens,
    required this.z,
    required this.sizeWeight,
    required this.neighbors,
  });

  factory DreamMapChunkDetail.fromJson(Map<String, dynamic> json) {
    final neighborsJson = json['neighbors'] as List<dynamic>? ?? const [];
    return DreamMapChunkDetail(
      id: json['id'] as String,
      dreamId: json['dream_id'] as String,
      clusterId: json['cluster_id'] as int,
      clusterLabel: json['cluster_label'] as String? ?? 'Unknown',
      archetypeColor: json['archetype_color'] as String? ?? '#98A2B3',
      text: json['text'] as String? ?? '',
      date: DateTime.parse(json['date'] as String),
      emotionValence: (json['emotion_valence'] as num?)?.toDouble() ?? 0.0,
      tokens: json['tokens'] as int? ?? 0,
      z: (json['z'] as num?)?.toDouble() ?? 0.0,
      sizeWeight: (json['size_weight'] as num?)?.toDouble() ?? 0.0,
      neighbors: neighborsJson
          .map(
            (item) => DreamMapNeighbor.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
    );
  }
}
