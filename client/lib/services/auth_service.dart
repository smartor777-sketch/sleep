import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config.dart';
import '../models/user_me.dart';
import 'secure_storage_service.dart';
import 'api_client.dart';

class AuthService {
  AuthService(this._storage) : _api = ApiClient(_storage);

  final SecureStorageService _storage;
  final ApiClient _api;

  Future<UserMe> anonymousAuth({required String deviceId}) async {
    final uri = Uri.parse('$apiBaseUrl/api/v1/auth/anonymous');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'device_id': deviceId,
        'platform': null,
        'app_version': null,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception('Anonymous auth failed');
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final accessToken = data['access_token'] as String?;
    final refreshToken = data['refresh_token'] as String?;
    if (accessToken == null || refreshToken == null) {
      throw Exception('Invalid auth response');
    }

    await _storage.setTokens(accessToken: accessToken, refreshToken: refreshToken);

    return getMe();
  }

  Future<UserMe> getMe() async {
    final response = await _api.get('/api/v1/users/me');
    if (response.statusCode != 200) {
      throw Exception('Failed to load user');
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return UserMe.fromJson(data);
  }

  Future<UserMe> linkProvider({required String provider, required String idToken}) async {
    final response = await _api.post(
      '/api/v1/auth/link',
      body: {
        'provider': provider,
        'id_token': idToken,
      },
    );

    if (response.statusCode == 409) {
      throw Exception('identity_already_linked');
    }
    if (response.statusCode != 200) {
      throw Exception('link_failed');
    }

    return getMe();
  }

  SecureStorageService get storage => _storage;
}
