import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:uuid/uuid.dart';

class SecureStorageService {
  static const _deviceIdKey = 'device_id';
  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';
  static const _darkModeKey = 'theme_dark_mode';
  static const _accentColorKey = 'theme_accent_color';

  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  final Uuid _uuid = const Uuid();

  Future<String> getOrCreateDeviceId() async {
    final existing = await _storage.read(key: _deviceIdKey);
    if (existing != null && existing.isNotEmpty) return existing;
    final id = _uuid.v4();
    await _storage.write(key: _deviceIdKey, value: id);
    return id;
  }

  Future<String?> getAccessToken() => _storage.read(key: _accessTokenKey);
  Future<String?> getRefreshToken() => _storage.read(key: _refreshTokenKey);

  Future<void> setTokens({required String accessToken, required String refreshToken}) async {
    await _storage.write(key: _accessTokenKey, value: accessToken);
    await _storage.write(key: _refreshTokenKey, value: refreshToken);
  }

  Future<bool> getDarkMode() async {
    final value = await _storage.read(key: _darkModeKey);
    return value == 'true';
  }

  Future<void> setDarkMode(bool value) async {
    await _storage.write(key: _darkModeKey, value: value.toString());
  }

  Future<Color?> getAccentColor() async {
    final value = await _storage.read(key: _accentColorKey);
    if (value == null) return null;
    final intVal = int.tryParse(value);
    if (intVal == null) return null;
    return Color(intVal);
  }

  Future<void> setAccentColor(Color color) async {
    await _storage.write(key: _accentColorKey, value: color.value.toString());
  }
}
