import 'dart:convert';

import 'api_client.dart';
import 'api_exception.dart';

class TranscriptionService {
  TranscriptionService(this._api);

  final ApiClient _api;

  Future<String> transcribeAudioFile(
    String filePath, {
    String? language,
    String? prompt,
  }) async {
    final fields = <String, String>{};
    if (language != null && language.isNotEmpty) {
      fields['language'] = language;
    }
    if (prompt != null && prompt.isNotEmpty) {
      fields['prompt'] = prompt;
    }

    final response = await _api.postMultipart(
      '/api/v1/audio/transcriptions',
      fileField: 'file',
      filePath: filePath,
      fields: fields,
    );
    final body = await response.stream.bytesToString();
    _ensureOk(response.statusCode, body);

    final data = jsonDecode(body) as Map<String, dynamic>;
    final text = data['text']?.toString().trim() ?? '';
    if (text.isEmpty) {
      throw ApiException(500, 'empty_transcription');
    }
    return text;
  }

  void _ensureOk(int statusCode, String body) {
    if (statusCode >= 200 && statusCode < 300) {
      return;
    }
    String message = 'request_failed';
    try {
      final data = jsonDecode(body) as Map<String, dynamic>;
      message = data['detail']?.toString() ?? message;
    } catch (_) {}
    throw ApiException(statusCode, message);
  }
}
