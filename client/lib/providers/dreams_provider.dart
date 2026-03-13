import 'package:flutter/material.dart';

import '../models/dream.dart';
import '../services/dreams_service.dart';
import 'auth_provider.dart';
import '../services/api_exception.dart';

class DreamsProvider extends ChangeNotifier {
  DreamsProvider(
    this._auth, {
    DreamsService? service,
    Duration pollInterval = const Duration(seconds: 2),
    int maxPollAttempts = 60,
  }) : _pollInterval = pollInterval,
       _maxPollAttempts = maxPollAttempts {
    _service = service ?? DreamsService(_auth.apiClient);
  }

  final AuthProvider _auth;
  final Duration _pollInterval;
  final int _maxPollAttempts;
  late final DreamsService _service;

  final List<Dream> _dreams = [];
  final List<Dream> _searchResults = [];
  bool _loading = false;
  bool _searching = false;
  String? _error;
  int? _errorCode;

  List<Dream> get dreams => List.unmodifiable(_dreams);
  List<Dream> get searchResults => List.unmodifiable(_searchResults);
  bool get loading => _loading;
  bool get searching => _searching;
  String? get error => _error;
  int? get errorCode => _errorCode;

  Future<void> loadDreams({String? date}) async {
    _loading = true;
    _error = null;
    _errorCode = null;
    notifyListeners();
    try {
      final items = await _service.getDreams(page: 1, pageSize: 50, date: date);
      _dreams
        ..clear()
        ..addAll(items);
    } catch (e) {
      if (e is ApiException) {
        _error = e.message;
        _errorCode = e.statusCode;
      } else {
        _error = 'network_error';
      }
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> search(String query, {String mode = 'semantic'}) async {
    if (query.isEmpty) {
      _searchResults.clear();
      notifyListeners();
      return;
    }
    _searching = true;
    _error = null;
    _errorCode = null;
    notifyListeners();
    try {
      final items = await _service.searchDreams(query, mode: mode);
      _searchResults
        ..clear()
        ..addAll(items);
    } catch (e) {
      if (e is ApiException) {
        _error = e.message;
        _errorCode = e.statusCode;
      } else {
        _error = 'network_error';
      }
    } finally {
      _searching = false;
      notifyListeners();
    }
  }

  Future<Dream?> createDream(String content) async {
    _error = null;
    _errorCode = null;
    final optimisticDream = _buildOptimisticDream(content);
    _dreams.insert(0, optimisticDream);
    notifyListeners();

    try {
      final dream = await _service.createDream(content);
      final localIndex = _dreams.indexWhere((d) => d.id == optimisticDream.id);
      if (localIndex >= 0) {
        _dreams[localIndex] = dream;
      } else {
        _dreams.insert(0, dream);
      }
      notifyListeners();
      _pollDreamUntilSettled(dream.id);
      return dream;
    } catch (e) {
      _dreams.removeWhere((d) => d.id == optimisticDream.id);
      if (e is ApiException) {
        _error = e.message;
        _errorCode = e.statusCode;
      } else {
        _error = 'network_error';
      }
      notifyListeners();
      return null;
    }
  }

  Dream _buildOptimisticDream(String content) {
    final now = DateTime.now().toUtc();
    final normalized = content.trim().replaceAll(RegExp(r'\s+'), ' ');
    final title = normalized.isEmpty
        ? null
        : normalized.substring(
            0,
            normalized.length > 64 ? 64 : normalized.length,
          );
    return Dream(
      id: 'local-${now.microsecondsSinceEpoch}',
      userId: _auth.user?.id ?? 'local-user',
      title: title,
      content: content,
      emoji: '',
      comment: '',
      recordedAt: now,
      createdAt: now,
      updatedAt: now,
      hasAnalysis: false,
      analysisStatus: 'analyzing',
      analysisErrorMessage: null,
      gradientColor1: null,
      gradientColor2: null,
    );
  }

  Future<Dream?> updateDream(String id, String content) async {
    try {
      final updated = await _service.updateDream(id, content);
      final index = _dreams.indexWhere((d) => d.id == id);
      if (index >= 0) {
        _dreams[index] = updated;
      }
      notifyListeners();
      return updated;
    } catch (e) {
      if (e is ApiException) {
        _error = e.message;
        _errorCode = e.statusCode;
      } else {
        _error = 'network_error';
      }
      notifyListeners();
      return null;
    }
  }

  Future<Dream?> updateDreamTitle(String id, String? title) async {
    try {
      final updated = await _service.updateDreamTitle(id, title);
      final index = _dreams.indexWhere((d) => d.id == id);
      if (index >= 0) {
        _dreams[index] = updated;
      }
      notifyListeners();
      return updated;
    } catch (e) {
      if (e is ApiException) {
        _error = e.message;
        _errorCode = e.statusCode;
      } else {
        _error = 'network_error';
      }
      notifyListeners();
      return null;
    }
  }

  Future<Dream?> updateDreamDate(String id, DateTime createdAt) async {
    try {
      final updated = await _service.updateDreamDate(id, createdAt);
      final index = _dreams.indexWhere((d) => d.id == id);
      if (index >= 0) {
        _dreams[index] = updated;
      }
      final searchIndex = _searchResults.indexWhere((d) => d.id == id);
      if (searchIndex >= 0) {
        _searchResults[searchIndex] = updated;
      }
      notifyListeners();
      return updated;
    } catch (e) {
      if (e is ApiException) {
        _error = e.message;
        _errorCode = e.statusCode;
      } else {
        _error = 'network_error';
      }
      notifyListeners();
      return null;
    }
  }

  Future<bool> deleteDream(String id) async {
    try {
      await _service.deleteDream(id);
      _dreams.removeWhere((d) => d.id == id);
      notifyListeners();
      return true;
    } catch (e) {
      if (e is ApiException) {
        _error = e.message;
        _errorCode = e.statusCode;
      } else {
        _error = 'network_error';
      }
      notifyListeners();
      return false;
    }
  }

  void clearError() {
    _error = null;
    _errorCode = null;
    notifyListeners();
  }

  Future<Dream?> refreshDream(String id) async {
    try {
      final updated = await _service.getDream(id);
      final index = _dreams.indexWhere((d) => d.id == id);
      if (index >= 0) {
        _dreams[index] = updated;
      }
      final searchIndex = _searchResults.indexWhere((d) => d.id == id);
      if (searchIndex >= 0) {
        _searchResults[searchIndex] = updated;
      }
      notifyListeners();
      return updated;
    } catch (e) {
      if (e is ApiException) {
        _error = e.message;
        _errorCode = e.statusCode;
      } else {
        _error = 'network_error';
      }
      notifyListeners();
      return null;
    }
  }

  Future<void> _pollDreamUntilSettled(String id) async {
    for (var i = 0; i < _maxPollAttempts; i++) {
      final updated = await refreshDream(id);
      final status = updated?.analysisStatus;
      if (status == null) return;
      if (status == 'analyzed' || status == 'analysis_failed') {
        return;
      }
      await Future.delayed(_pollInterval);
    }
  }
}
