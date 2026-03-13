import 'package:flutter/material.dart';

import '../models/dream_map.dart';
import '../services/api_exception.dart';
import '../services/dream_map_service.dart';
import 'auth_provider.dart';

class DreamMapProvider extends ChangeNotifier {
  DreamMapProvider(this._auth, {DreamMapService? service}) {
    _service = service ?? DreamMapService(_auth.apiClient);
  }

  final AuthProvider _auth;
  late final DreamMapService _service;

  DreamMapData? _map;
  bool _loading = false;
  bool _detailLoading = false;
  String? _error;
  DreamMapChunkDetail? _selectedDetail;
  String? _selectedCluster;

  DreamMapData? get map => _map;
  bool get loading => _loading;
  bool get detailLoading => _detailLoading;
  String? get error => _error;
  DreamMapChunkDetail? get selectedDetail => _selectedDetail;
  String? get selectedCluster => _selectedCluster;

  List<DreamMapNode> get visibleNodes {
    final nodes = _map?.nodes ?? const <DreamMapNode>[];
    final cluster = _selectedCluster;
    if (cluster == null || cluster.isEmpty) {
      return nodes;
    }
    return nodes.where((node) => node.clusterLabel == cluster).toList();
  }

  Future<void> load({bool forceRefresh = false}) async {
    final userId = _auth.user?.id;
    if (userId == null) return;
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      _map = await _service.getMap(userId, forceRefresh: forceRefresh);
    } catch (e) {
      if (e is ApiException) {
        _error = e.message;
      } else {
        _error = 'network_error';
      }
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> selectNode(String chunkId) async {
    final userId = _auth.user?.id;
    if (userId == null) return;
    _detailLoading = true;
    _error = null;
    notifyListeners();
    try {
      _selectedDetail = await _service.getChunkDetail(userId, chunkId);
    } catch (e) {
      if (e is ApiException) {
        _error = e.message;
      } else {
        _error = 'network_error';
      }
    } finally {
      _detailLoading = false;
      notifyListeners();
    }
  }

  void setClusterFilter(String? clusterLabel) {
    _selectedCluster = clusterLabel;
    notifyListeners();
  }

  void clearSelection() {
    _selectedDetail = null;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
