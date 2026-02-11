import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/analysis_message.dart';
import 'api_client.dart';
import 'api_exception.dart';

class SendMessageResult {
  final String taskId;
  final String status;
  final AnalysisMessage userMessage;

  SendMessageResult({
    required this.taskId,
    required this.status,
    required this.userMessage,
  });
}

class MessagesService {
  MessagesService(this._api);

  final ApiClient _api;

  Future<List<AnalysisMessage>> getMessages(String dreamId, {int limit = 200, int offset = 0}) async {
    final response = await _api.get('/api/v1/messages/dream/$dreamId?limit=$limit&offset=$offset');
    _ensureOk(response);
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final items = data['messages'] as List<dynamic>? ?? [];
    return items.map((e) => AnalysisMessage.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<SendMessageResult> sendMessage(String dreamId, String content) async {
    final response = await _api.post(
      '/api/v1/messages',
      body: {
        'dream_id': dreamId,
        'content': content,
      },
    );
    if (response.statusCode != 202) {
      _throwApi(response);
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return SendMessageResult(
      taskId: data['task_id'] as String,
      status: data['status'] as String,
      userMessage: AnalysisMessage.fromJson(
        data['user_message'] as Map<String, dynamic>,
      ),
    );
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
