import 'dart:convert';

import 'dart:convert';
import 'package:http/http.dart' as http;

import '../models/dream.dart';
import 'api_client.dart';
import 'api_exception.dart';

class DreamsService {
  DreamsService(this._api);

  final ApiClient _api;

  Future<List<Dream>> getDreams({int page = 1, int pageSize = 50, String? date}) async {
    final dateParam = date != null ? '&date=$date' : '';
    final response = await _api.get('/api/v1/dreams?page=$page&page_size=$pageSize$dateParam');
    _ensureOk(response);
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final dreamsJson = data['dreams'] as List<dynamic>? ?? [];
    return dreamsJson.map((e) => Dream.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<Dream>> searchDreams(String query) async {
    final encoded = Uri.encodeQueryComponent(query);
    final response = await _api.get('/api/v1/dreams/search?q=$encoded');
    _ensureOk(response);
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final dreamsJson = data['dreams'] as List<dynamic>? ?? [];
    return dreamsJson.map((e) => Dream.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Dream> createDream(String content) async {
    final response = await _api.post(
      '/api/v1/dreams',
      body: {
        'content': content,
      },
    );
    if (response.statusCode != 201) {
      _throwApi(response);
    }
    return Dream.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<Dream> updateDream(String id, String content) async {
    final response = await _api.put(
      '/api/v1/dreams/$id',
      body: {
        'content': content,
      },
    );
    _ensureOk(response);
    return Dream.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<Dream> updateDreamTitle(String id, String? title) async {
    final response = await _api.put(
      '/api/v1/dreams/$id',
      body: {
        'title': title,
      },
    );
    _ensureOk(response);
    return Dream.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<void> deleteDream(String id) async {
    final response = await _api.delete('/api/v1/dreams/$id');
    _ensureOk(response);
  }

  void _ensureOk(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) return;
    _throwApi(response);
  }

  void _throwApi(http.Response response) {
    String message = 'request_failed';
    try {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      message = data['detail']?.toString() ?? message;
    } catch (_) {}
    throw ApiException(response.statusCode, message);
  }
}
