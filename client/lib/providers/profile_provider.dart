import 'package:flutter/material.dart';

import '../models/user_me.dart';
import '../services/stats_service.dart';
import '../services/users_service.dart';
import 'auth_provider.dart';
import '../services/api_exception.dart';

class ProfileProvider extends ChangeNotifier {
  ProfileProvider(this._auth) {
    _statsService = StatsService(_auth.apiClient);
    _usersService = UsersService(_auth.apiClient);
  }

  final AuthProvider _auth;
  late final StatsService _statsService;
  late final UsersService _usersService;

  Stats? _stats;
  bool _loading = false;
  String? _error;

  Stats? get stats => _stats;
  bool get loading => _loading;
  String? get error => _error;

  Future<void> loadStats() async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      _stats = await _statsService.getMyStats();
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

  Future<UserMe?> saveAboutMe(String aboutMe) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      final updated = await _usersService.updateMe(aboutMe: aboutMe);
      _auth.updateUser(updated);
      return updated;
    } catch (e) {
      if (e is ApiException) {
        _error = e.message;
      } else {
        _error = 'network_error';
      }
      return null;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
