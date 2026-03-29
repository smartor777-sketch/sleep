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
      // Try existing token first
      final existingToken = await _authService.storage.getAccessToken();
      if (existingToken != null) {
        try {
          _user = await _authService.getMe();
          return;
        } catch (_) {
          // Token expired or invalid — fall through to anonymous auth
        }
      }
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

  /// Register with email/password. Returns the new user.
  /// Caller should then navigate to verify-email screen.
  Future<UserMe> registerWithEmail({
    required String email,
    required String password,
  }) async {
    final user = await _authService.register(email: email, password: password);
    _user = user;
    notifyListeners();
    return user;
  }

  /// Login with email/password.
  Future<UserMe> loginWithEmail({
    required String email,
    required String password,
  }) async {
    final user = await _authService.login(email: email, password: password);
    _user = user;
    notifyListeners();
    return user;
  }

  /// Verify email with 6-digit code.
  Future<void> verifyEmail({required String email, required String code}) async {
    await _authService.verifyEmailCode(email: email, code: code);
    if (_user != null) {
      _user = _user!.copyWith(emailVerified: true);
      notifyListeners();
    }
  }

  /// Merge anonymous account data into the current registered account.
  Future<void> mergeAnonymous() async {
    final deviceId = await _authService.storage.getOrCreateDeviceId();
    await _authService.mergeAnonymous(deviceId: deviceId);
  }

  /// Sign in with Google.
  Future<UserMe> signInWithGoogle() async {
    await mergeAnonymous();
    final user = await _authService.signInWithGoogle();
    _user = user;
    notifyListeners();
    return user;
  }

  /// Logout — clear tokens and bootstrap anonymously.
  Future<void> logout() async {
    await _authService.logout();
    _user = null;
    _loading = false;
    _error = null;
    notifyListeners();
    await bootstrap();
  }

  void updateUser(UserMe user) {
    _user = user;
    notifyListeners();
  }
}
