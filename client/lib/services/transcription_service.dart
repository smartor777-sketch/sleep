import 'dart:convert';

import 'api_client.dart';
import 'api_exception.dart';

class TranscriptionResult {
  final String text;
  final bool partial;
  final int segmentsTotal;
  final int segmentsOk;
  final int segmentsFailed;

  TranscriptionResult({
    required this.text,
    this.partial = false,
    this.segmentsTotal = 1,
    this.segmentsOk = 1,
    this.segmentsFailed = 0,
  });
}

class TranscriptionService {
  TranscriptionService(this._api);

  final ApiClient _api;

  Future<TranscriptionResult> transcribeAudioFile(
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
    return TranscriptionResult(
      text: text,
      partial: data['partial'] as bool? ?? false,
      segmentsTotal: data['segments_total'] as int? ?? 1,
      segmentsOk: data['segments_ok'] as int? ?? 1,
      segmentsFailed: data['segments_failed'] as int? ?? 0,
    );
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
