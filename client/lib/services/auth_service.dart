import 'dart:convert';

import 'package:google_sign_in/google_sign_in.dart';
import 'package:http/http.dart' as http;

import '../config.dart';
import '../models/user_me.dart';
import '../version.dart';
import 'secure_storage_service.dart';
import 'api_client.dart';

class AuthService {
  AuthService(
    this._storage, {
    ApiClient? apiClient,
    http.Client? httpClient,
  })  : _api = apiClient ?? ApiClient(_storage, httpClient: httpClient),
        _httpClient = httpClient ?? http.Client();

  final SecureStorageService _storage;
  final ApiClient _api;
  final http.Client _httpClient;

  Future<UserMe> anonymousAuth({required String deviceId}) async {
    final uri = Uri.parse('$apiBaseUrl/api/v1/auth/anonymous');
    final response = await _httpClient.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'X-App-Version': appVersion,
      },
      body: jsonEncode({
        'device_id': deviceId,
        'platform': null,
        'app_version': appVersion,
      }),
    );

    if (response.statusCode == 426) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      throw UpgradeRequiredException(
        minVersion: data['min_version'] as String? ?? '',
        downloadUrl: data['download_url'] as String? ?? '',
      );
    }

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

  Future<UserMe> register({required String email, required String password}) async {
    final response = await _api.post(
      '/api/v1/auth/register',
      body: {'email': email, 'password': password},
      auth: false,
    );
    if (response.statusCode == 400) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      throw Exception(data['detail'] ?? 'registration_failed');
    }
    if (response.statusCode != 201) {
      throw Exception('registration_failed');
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    await _storage.setTokens(
      accessToken: data['access_token'] as String,
      refreshToken: data['refresh_token'] as String,
    );
    return getMe();
  }

  Future<UserMe> login({required String email, required String password}) async {
    final response = await _api.post(
      '/api/v1/auth/login',
      body: {'email': email, 'password': password},
      auth: false,
    );
    if (response.statusCode == 401) {
      throw Exception('invalid_credentials');
    }
    if (response.statusCode != 200) {
      throw Exception('login_failed');
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    await _storage.setTokens(
      accessToken: data['access_token'] as String,
      refreshToken: data['refresh_token'] as String,
    );
    return getMe();
  }

  Future<void> verifyEmailCode({required String email, required String code}) async {
    final response = await _api.post(
      '/api/v1/auth/verify-email-code',
      body: {'email': email, 'code': code},
      auth: false,
    );
    if (response.statusCode != 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      throw Exception(data['detail'] ?? 'invalid_code');
    }
  }

  Future<void> resendCode({required String email}) async {
    await _api.post(
      '/api/v1/auth/resend-code',
      body: {'email': email},
      auth: false,
    );
  }

  Future<bool> mergeAnonymous({required String deviceId}) async {
    final response = await _api.post(
      '/api/v1/auth/merge-anonymous',
      body: {'anonymous_device_id': deviceId},
    );
    return response.statusCode == 200;
  }

  Future<void> logout() async {
    try {
      await _api.post('/api/v1/auth/logout', body: const {});
    } catch (_) {
      // logout всегда успешен с точки зрения клиента — токены чистим в любом случае
    }
    await _storage.clearTokens();
  }

  Future<void> forgotPassword({required String email}) async {
    final response = await _api.post(
      '/api/v1/auth/forgot-password',
      body: {'email': email},
      auth: false,
    );
    if (response.statusCode == 400) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      throw Exception(data['detail'] ?? 'oauth_account_no_password');
    }
    if (response.statusCode != 200) {
      throw Exception('forgot_password_failed');
    }
  }

  Future<void> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    final response = await _api.post(
      '/api/v1/auth/reset-password',
      body: {'token': token, 'new_password': newPassword},
      auth: false,
    );
    if (response.statusCode == 400) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      throw Exception(data['detail'] ?? 'invalid_or_expired_token');
    }
    if (response.statusCode != 200) {
      throw Exception('reset_password_failed');
    }
  }

  Future<void> deleteAccount() async {
    final response = await _api.delete('/api/v1/auth/account');
    if (response.statusCode != 200) {
      throw Exception('delete_account_failed');
    }
    await _storage.clearTokens();
  }

  Future<UserMe> signInWithGoogle() async {
    final googleSignIn = GoogleSignIn(
      serverClientId: googleWebClientId.isNotEmpty ? googleWebClientId : null,
    );
    final account = await googleSignIn.signIn();
    if (account == null) throw Exception('google_sign_in_cancelled');

    final auth = await account.authentication;
    final idToken = auth.idToken;
    if (idToken == null) throw Exception('google_id_token_null');

    final response = await _api.post(
      '/api/v1/auth/google',
      body: {'id_token': idToken},
    );
    if (response.statusCode != 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      throw Exception(data['detail'] ?? 'google_signin_failed');
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    await _storage.setTokens(
      accessToken: data['access_token'] as String,
      refreshToken: data['refresh_token'] as String,
    );
    return getMe();
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

  /// Telegram deep-link auth — step 1: ask backend for short-lived token
  /// and a https://t.me/<bot>?start=<token> deeplink.
  Future<TelegramInitResult> telegramInit() async {
    final response = await _api.post('/api/v1/auth/telegram/init', body: const {});
    if (response.statusCode != 200) {
      throw Exception('telegram_init_failed');
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return TelegramInitResult(
      authToken: data['auth_token'] as String,
      deeplink: data['deeplink'] as String,
      botUsername: data['bot_username'] as String? ?? '',
      expiresIn: data['expires_in'] as int? ?? 600,
    );
  }

  /// Telegram deep-link auth — step 2: poll status until the bot confirms.
  /// Returns null while pending, throws on expired, returns tokens on completion.
  /// On completion the access/refresh tokens are written to secure storage.
  Future<TelegramStatusResult> telegramStatus(String authToken) async {
    final response = await _api.get(
      '/api/v1/auth/telegram/status?auth_token=${Uri.encodeQueryComponent(authToken)}',
    );
    if (response.statusCode != 200) {
      throw Exception('telegram_status_failed');
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final status = data['status'] as String? ?? 'pending';
    if (status == 'completed') {
      final access = data['access_token'] as String?;
      final refresh = data['refresh_token'] as String?;
      if (access != null && refresh != null) {
        await _storage.setTokens(accessToken: access, refreshToken: refresh);
      }
      return TelegramStatusResult(status: 'completed');
    }
    return TelegramStatusResult(status: status);
  }

  Future<VkInitResult> vkInit() async {
    final response = await _api.post('/api/v1/auth/vk/init', body: const {});
    if (response.statusCode != 200) throw Exception('vk_init_failed');
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return VkInitResult(
      state: data['state'] as String,
      authUrl: data['auth_url'] as String,
      expiresIn: data['expires_in'] as int? ?? 600,
    );
  }

  Future<VkStatusResult> vkStatus(String state) async {
    final response = await _api.get(
      '/api/v1/auth/vk/status?state=${Uri.encodeQueryComponent(state)}',
    );
    if (response.statusCode != 200) throw Exception('vk_status_failed');
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final status = data['status'] as String? ?? 'pending';
    if (status == 'completed') {
      final access = data['access_token'] as String?;
      final refresh = data['refresh_token'] as String?;
      if (access != null && refresh != null) {
        await _storage.setTokens(accessToken: access, refreshToken: refresh);
      }
      return VkStatusResult(status: 'completed');
    }
    return VkStatusResult(status: status);
  }

  Future<YandexInitResult> yandexInit() async {
    final response = await _api.post('/api/v1/auth/yandex/init', body: const {});
    if (response.statusCode != 200) throw Exception('yandex_init_failed');
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return YandexInitResult(
      state: data['state'] as String,
      authUrl: data['auth_url'] as String,
      expiresIn: data['expires_in'] as int? ?? 600,
    );
  }

  Future<YandexStatusResult> yandexStatus(String state) async {
    final response = await _api.get(
      '/api/v1/auth/yandex/status?state=${Uri.encodeQueryComponent(state)}',
    );
    if (response.statusCode != 200) throw Exception('yandex_status_failed');
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final status = data['status'] as String? ?? 'pending';
    if (status == 'completed') {
      final access = data['access_token'] as String?;
      final refresh = data['refresh_token'] as String?;
      if (access != null && refresh != null) {
        await _storage.setTokens(accessToken: access, refreshToken: refresh);
      }
      return YandexStatusResult(status: 'completed');
    }
    return YandexStatusResult(status: status);
  }
}

class VkInitResult {
  final String state;
  final String authUrl;
  final int expiresIn;

  VkInitResult({required this.state, required this.authUrl, required this.expiresIn});
}

class VkStatusResult {
  final String status;
  VkStatusResult({required this.status});
}

class YandexInitResult {
  final String state;
  final String authUrl;
  final int expiresIn;

  YandexInitResult({
    required this.state,
    required this.authUrl,
    required this.expiresIn,
  });
}

class YandexStatusResult {
  final String status;
  YandexStatusResult({required this.status});
}

class TelegramInitResult {
  final String authToken;
  final String deeplink;
  final String botUsername;
  final int expiresIn;

  TelegramInitResult({
    required this.authToken,
    required this.deeplink,
    required this.botUsername,
    required this.expiresIn,
  });
}

class TelegramStatusResult {
  /// 'pending' | 'completed' | 'expired'
  final String status;
  TelegramStatusResult({required this.status});
}

class UpgradeRequiredException implements Exception {
  final String minVersion;
  final String downloadUrl;

  UpgradeRequiredException({required this.minVersion, required this.downloadUrl});

  @override
  String toString() => 'upgrade_required';
}
