import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config.dart';
import '../version.dart';
import 'secure_storage_service.dart';

class ApiClient {
  ApiClient(this._storage, {http.Client? httpClient})
    : _httpClient = httpClient ?? http.Client();

  final SecureStorageService _storage;
  final http.Client _httpClient;

  Future<http.Response> get(String path, {bool auth = true}) async {
    return _request('GET', path, auth: auth);
  }

  Future<http.Response> post(
    String path, {
    Object? body,
    bool auth = true,
  }) async {
    return _request('POST', path, body: body, auth: auth);
  }

  Future<http.Response> put(
    String path, {
    Object? body,
    bool auth = true,
  }) async {
    return _request('PUT', path, body: body, auth: auth);
  }

  Future<http.Response> patch(
    String path, {
    Object? body,
    bool auth = true,
  }) async {
    return _request('PATCH', path, body: body, auth: auth);
  }

  Future<http.Response> delete(String path, {bool auth = true}) async {
    return _request('DELETE', path, auth: auth);
  }

  Future<http.StreamedResponse> postMultipart(
    String path, {
    required String fileField,
    required String filePath,
    Map<String, String>? fields,
    bool auth = true,
  }) async {
    final uri = Uri.parse('$apiBaseUrl$path');

    Future<http.MultipartRequest> buildRequest({required bool withAuth}) async {
      final request = http.MultipartRequest('POST', uri);
      request.headers.addAll(
        await _buildHeaders(withAuth: withAuth, json: false),
      );
      if (fields != null) {
        request.fields.addAll(fields);
      }
      request.files.add(await http.MultipartFile.fromPath(fileField, filePath));
      return request;
    }

    var response = await _httpClient.send(await buildRequest(withAuth: auth));

    if (response.statusCode == 401 && auth) {
      final refreshed = await _refreshToken();
      if (refreshed) {
        response = await _httpClient.send(await buildRequest(withAuth: true));
      }
    }

    return response;
  }

  Future<http.Response> _request(
    String method,
    String path, {
    Object? body,
    bool auth = true,
  }) async {
    final uri = Uri.parse('$apiBaseUrl$path');

    http.Response response;
    if (method == 'GET') {
      response = await _httpClient.get(
        uri,
        headers: await _buildHeaders(withAuth: auth),
      );
    } else if (method == 'POST') {
      response = await _httpClient.post(
        uri,
        headers: await _buildHeaders(withAuth: auth),
        body: body == null ? null : jsonEncode(body),
      );
    } else if (method == 'PUT') {
      response = await _httpClient.put(
        uri,
        headers: await _buildHeaders(withAuth: auth),
        body: body == null ? null : jsonEncode(body),
      );
    } else if (method == 'DELETE') {
      response = await _httpClient.delete(
        uri,
        headers: await _buildHeaders(withAuth: auth),
      );
    } else if (method == 'PATCH') {
      response = await _httpClient.patch(
        uri,
        headers: await _buildHeaders(withAuth: auth),
        body: body == null ? null : jsonEncode(body),
      );
    } else {
      throw UnsupportedError('Unsupported method: $method');
    }

    if (response.statusCode == 401 && auth) {
      final refreshed = await _refreshToken();
      if (refreshed) {
        if (method == 'GET') {
          return _httpClient.get(
            uri,
            headers: await _buildHeaders(withAuth: true),
          );
        }
        if (method == 'POST') {
          return _httpClient.post(
            uri,
            headers: await _buildHeaders(withAuth: true),
            body: body == null ? null : jsonEncode(body),
          );
        }
        if (method == 'PUT') {
          return _httpClient.put(
            uri,
            headers: await _buildHeaders(withAuth: true),
            body: body == null ? null : jsonEncode(body),
          );
        }
        if (method == 'DELETE') {
          return _httpClient.delete(
            uri,
            headers: await _buildHeaders(withAuth: true),
          );
        }
        if (method == 'PATCH') {
          return _httpClient.patch(
            uri,
            headers: await _buildHeaders(withAuth: true),
            body: body == null ? null : jsonEncode(body),
          );
        }
      }
    }

    return response;
  }

  Future<Map<String, String>> _buildHeaders({
    required bool withAuth,
    bool json = true,
  }) async {
    final headers = <String, String>{
      'X-App-Version': appVersion,
    };
    if (json) {
      headers['Content-Type'] = 'application/json';
    }
    if (withAuth) {
      final token = await _storage.getAccessToken();
      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
      }
    }
    return headers;
  }

  Future<bool> _refreshToken() async {
    final refreshToken = await _storage.getRefreshToken();
    if (refreshToken == null) return false;

    final uri = Uri.parse('$apiBaseUrl/api/v1/auth/refresh');
    final response = await _httpClient.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'refresh_token': refreshToken}),
    );

    if (response.statusCode != 200) return false;

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final accessToken = data['access_token'] as String?;
    final newRefresh = data['refresh_token'] as String?;
    if (accessToken == null || newRefresh == null) return false;

    await _storage.setTokens(
      accessToken: accessToken,
      refreshToken: newRefresh,
    );
    return true;
  }
}
