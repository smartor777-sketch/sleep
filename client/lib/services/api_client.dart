import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config.dart';
import 'secure_storage_service.dart';

class ApiClient {
  ApiClient(this._storage);

  final SecureStorageService _storage;

  Future<http.Response> get(String path, {bool auth = true}) async {
    return _request('GET', path, auth: auth);
  }

  Future<http.Response> post(String path, {Object? body, bool auth = true}) async {
    return _request('POST', path, body: body, auth: auth);
  }

  Future<http.Response> put(String path, {Object? body, bool auth = true}) async {
    return _request('PUT', path, body: body, auth: auth);
  }

  Future<http.Response> delete(String path, {bool auth = true}) async {
    return _request('DELETE', path, auth: auth);
  }

  Future<http.Response> _request(
    String method,
    String path, {
    Object? body,
    bool auth = true,
  }) async {
    final uri = Uri.parse('$apiBaseUrl$path');

    Future<Map<String, String>> buildHeaders({required bool withAuth}) async {
      final headers = <String, String>{'Content-Type': 'application/json'};
      if (withAuth) {
        final token = await _storage.getAccessToken();
        if (token != null) headers['Authorization'] = 'Bearer $token';
      }
      return headers;
    }

    http.Response response;
    if (method == 'GET') {
      response = await http.get(uri, headers: await buildHeaders(withAuth: auth));
    } else if (method == 'POST') {
      response = await http.post(
        uri,
        headers: await buildHeaders(withAuth: auth),
        body: body == null ? null : jsonEncode(body),
      );
    } else if (method == 'PUT') {
      response = await http.put(
        uri,
        headers: await buildHeaders(withAuth: auth),
        body: body == null ? null : jsonEncode(body),
      );
    } else if (method == 'DELETE') {
      response = await http.delete(
        uri,
        headers: await buildHeaders(withAuth: auth),
      );
    } else {
      throw UnsupportedError('Unsupported method: $method');
    }

    if (response.statusCode == 401 && auth) {
      final refreshed = await _refreshToken();
      if (refreshed) {
        if (method == 'GET') {
          return http.get(uri, headers: await buildHeaders(withAuth: true));
        }
        if (method == 'POST') {
          return http.post(
            uri,
            headers: await buildHeaders(withAuth: true),
            body: body == null ? null : jsonEncode(body),
          );
        }
        if (method == 'PUT') {
          return http.put(
            uri,
            headers: await buildHeaders(withAuth: true),
            body: body == null ? null : jsonEncode(body),
          );
        }
        if (method == 'DELETE') {
          return http.delete(
            uri,
            headers: await buildHeaders(withAuth: true),
          );
        }
      }
    }

    return response;
  }

  Future<bool> _refreshToken() async {
    final refreshToken = await _storage.getRefreshToken();
    if (refreshToken == null) return false;

    final uri = Uri.parse('$apiBaseUrl/api/v1/auth/refresh');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'refresh_token': refreshToken}),
    );

    if (response.statusCode != 200) return false;

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final accessToken = data['access_token'] as String?;
    final newRefresh = data['refresh_token'] as String?;
    if (accessToken == null || newRefresh == null) return false;

    await _storage.setTokens(accessToken: accessToken, refreshToken: newRefresh);
    return true;
  }
}
