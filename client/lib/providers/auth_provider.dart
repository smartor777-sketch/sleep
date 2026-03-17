import 'package:flutter/material.dart';

import '../models/user_me.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../services/secure_storage_service.dart';

export '../services/auth_service.dart' show UpgradeRequiredException;

class AuthProvider extends ChangeNotifier {
  AuthProvider({
    AuthService? authService,
    ApiClient? apiClient,
  }) {
    _authService = authService ?? AuthService(SecureStorageService());
    _apiClient = apiClient ?? ApiClient(_authService.storage);
  }

  late final AuthService _authService;
  late final ApiClient _apiClient;

  UserMe? _user;
  bool _loading = false;
  String? _error;
  UpgradeRequiredException? _upgradeRequired;

  UserMe? get user => _user;
  bool get loading => _loading;
  String? get error => _error;
  UpgradeRequiredException? get upgradeRequired => _upgradeRequired;
  AuthService get authService => _authService;
  ApiClient get apiClient => _apiClient;

  Future<void> bootstrap() async {
    if (_loading) return;
    _loading = true;
    _error = null;
    // Don't notifyListeners() here — bootstrap is called during build().
    // The loading state will be picked up on the next rebuild after the
    // async work completes.

    try {
      final deviceId = await _authService.storage.getOrCreateDeviceId();
      _user = await _authService.anonymousAuth(deviceId: deviceId);
    } on UpgradeRequiredException catch (e) {
      _upgradeRequired = e;
      _error = e.toString();
    } catch (e) {
      _error = e.toString();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  void updateUser(UserMe user) {
    _user = user;
    notifyListeners();
  }
}
