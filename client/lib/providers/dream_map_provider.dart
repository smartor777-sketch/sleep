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
  bool _refreshing = false;
  bool _detailLoading = false;
  String? _error;
  DreamMapSymbolDetail? _selectedDetail;
  String? _selectedArchetype;

  DreamMapData? get map => _map;
  bool get loading => _loading;
  bool get refreshing => _refreshing;
  bool get detailLoading => _detailLoading;
  String? get error => _error;
  DreamMapSymbolDetail? get selectedDetail => _selectedDetail;
  String? get selectedArchetype => _selectedArchetype;

  List<DreamMapNode> get visibleNodes {
    final nodes = _map?.nodes ?? const <DreamMapNode>[];
    final archetype = _selectedArchetype;
    if (archetype == null || archetype.isEmpty) {
      return nodes;
    }
    return nodes
        .where((node) => node.relatedArchetypes.contains(archetype))
        .toList();
  }

  Future<void> load({bool forceRefresh = false}) async {
    final userId = _auth.user?.id;
    if (userId == null) return;
    final hasMap = _map != null;
    _loading = !hasMap;
    _refreshing = hasMap && forceRefresh;
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
      _refreshing = false;
      notifyListeners();
    }
  }

  Future<void> selectNode(String nodeId) async {
    final userId = _auth.user?.id;
    if (userId == null) return;
    _detailLoading = true;
    _error = null;
    notifyListeners();
    try {
      _selectedDetail = await _service.getSymbolDetail(userId, nodeId);
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

  void setArchetypeFilter(String? archetype) {
    _selectedArchetype = archetype;
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
