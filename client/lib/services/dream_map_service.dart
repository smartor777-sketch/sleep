import 'dart:convert';

import '../models/dream_map.dart';
import 'api_client.dart';
import 'api_exception.dart';

class DreamMapService {
  DreamMapService(this._api);

  final ApiClient _api;

  Future<DreamMapData> getMap(
    String userId, {
    bool forceRefresh = false,
    int nNeighbors = 15,
    double minDist = 0.08,
    String clusterMethod = 'dbscan',
  }) async {
    final response = await _api.get(
      '/api/v1/map/$userId?n_neighbors=$nNeighbors&min_dist=$minDist&cluster_method=$clusterMethod&force_refresh=$forceRefresh',
    );
    _ensureOk(response.statusCode, response.body);
    return DreamMapData.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<DreamMapChunkDetail> getChunkDetail(
    String userId,
    String chunkId,
  ) async {
    final response = await _api.get('/api/v1/map/$userId/chunk/$chunkId');
    _ensureOk(response.statusCode, response.body);
    return DreamMapChunkDetail.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  void _ensureOk(int statusCode, String body) {
    if (statusCode >= 200 && statusCode < 300) return;
    var message = 'request_failed';
    try {
      final data = jsonDecode(body) as Map<String, dynamic>;
      message = data['detail']?.toString() ?? message;
    } catch (_) {}
    throw ApiException(statusCode, message);
  }
}
