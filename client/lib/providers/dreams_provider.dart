import 'package:flutter/material.dart';

import '../models/dream.dart';
import '../services/dreams_service.dart';
import 'auth_provider.dart';
import '../services/api_exception.dart';

class DreamsProvider extends ChangeNotifier {
  DreamsProvider(this._auth) {
    _service = DreamsService(_auth.apiClient);
  }

  final AuthProvider _auth;
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

  Future<void> search(String query) async {
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
      final items = await _service.searchDreams(query);
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
    try {
      final dream = await _service.createDream(content);
      _dreams.add(dream);
      notifyListeners();
      return dream;
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
}
