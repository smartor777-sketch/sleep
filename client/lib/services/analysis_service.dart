import 'dart:convert';

import 'package:http/http.dart' as http;

import 'api_client.dart';
import 'api_exception.dart';

class AnalysisTask {
  final String analysisId;
  final String taskId;
  final String status;

  AnalysisTask({
    required this.analysisId,
    required this.taskId,
    required this.status,
  });
}

class TaskStatus {
  final String status;
  final String? result;
  final String? error;

  TaskStatus({required this.status, this.result, this.error});
}

class MessageTaskStatus {
  final String status;
  final String? result;
  final String? error;

  MessageTaskStatus({required this.status, this.result, this.error});
}

class AnalysisService {
  AnalysisService(this._api);

  final ApiClient _api;

  Future<AnalysisTask> createAnalysis(String dreamId) async {
    final response = await _api.post(
      '/api/v1/analyses',
      body: {'dream_id': dreamId},
    );
    if (response.statusCode != 202) {
      _throwApi(response);
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return AnalysisTask(
      analysisId: data['analysis_id'] as String,
      taskId: data['task_id'] as String,
      status: data['status'] as String,
    );
  }

  Future<TaskStatus> getTaskStatus(String taskId) async {
    final response = await _api.get('/api/v1/analyses/task/$taskId');
    if (response.statusCode != 200) {
      _throwApi(response);
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return TaskStatus(
      status: data['status'] as String,
      result: data['result'] as String?,
      error: data['error'] as String?,
    );
  }

  Future<MessageTaskStatus> getMessageTaskStatus(String taskId) async {
    final response = await _api.get('/api/v1/messages/task/$taskId');
    if (response.statusCode != 200) {
      _throwApi(response);
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return MessageTaskStatus(
      status: data['status'] as String,
      result: data['result'] as String?,
      error: data['error'] as String?,
    );
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
