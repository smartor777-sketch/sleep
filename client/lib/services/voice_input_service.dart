import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

import 'api_client.dart';
import 'transcription_service.dart';

/// Shared voice recording + transcription service.
///
/// Used by both main_chat_screen (dream input) and analysis_chat_screen (chat input).
class VoiceInputService {
  VoiceInputService({required this.apiClient});

  final ApiClient apiClient;

  final AudioRecorder _recorder = AudioRecorder();
  StreamSubscription<Amplitude>? _amplitudeSubscription;
  Timer? _warningTimer;

  bool isRecording = false;
  bool isTranscribing = false;
  double recordingLevel = 0.18;
  String? _currentPath;

  VoidCallback? onStateChanged;
  VoidCallback? onRecordingWarning;

  static const Duration _warningDuration = Duration(seconds: 60);

  Future<void> toggleRecording() async {
    if (isTranscribing) return;
    if (isRecording) {
      await stopRecording();
    } else {
      await startRecording();
    }
  }

  Future<bool> startRecording() async {
    final hasPermission = await _recorder.hasPermission();
    if (!hasPermission) return false;

    final directory = await getTemporaryDirectory();
    _currentPath =
        '${directory.path}/voice_${DateTime.now().millisecondsSinceEpoch}.m4a';

    await _amplitudeSubscription?.cancel();
    _amplitudeSubscription = _recorder
        .onAmplitudeChanged(const Duration(milliseconds: 120))
        .listen((amplitude) {
      final normalized =
          ((amplitude.current + 45) / 45).clamp(0.08, 1.0).toDouble();
      recordingLevel = normalized;
      onStateChanged?.call();
    });

    await _recorder.start(
      const RecordConfig(
        encoder: AudioEncoder.aacLc,
        bitRate: 128000,
        sampleRate: 44100,
      ),
      path: _currentPath!,
    );

    isRecording = true;
    recordingLevel = 0.22;
    onStateChanged?.call();

    _warningTimer?.cancel();
    _warningTimer = Timer(_warningDuration, () {
      if (isRecording) {
        onRecordingWarning?.call();
      }
    });

    return true;
  }

  /// Stop recording and return file path, or null if nothing recorded.
  Future<String?> stopRecording() async {
    _warningTimer?.cancel();
    _warningTimer = null;

    await _amplitudeSubscription?.cancel();
    _amplitudeSubscription = null;

    final path = await _recorder.stop();
    isRecording = false;
    recordingLevel = 0.18;
    onStateChanged?.call();

    if (path == null || path.isEmpty) return null;
    return path;
  }

  /// Stop recording, transcribe, and return result.
  /// Appends to [existingText] if non-empty.
  Future<TranscriptionResult?> stopAndTranscribe({
    required String languageCode,
  }) async {
    final path = await stopRecording();
    if (path == null) return null;

    isTranscribing = true;
    onStateChanged?.call();

    try {
      final service = TranscriptionService(apiClient);
      final result = await service.transcribeAudioFile(
        path,
        language: languageCode,
      );
      return result;
    } finally {
      isTranscribing = false;
      onStateChanged?.call();
      _cleanupFile(path);
    }
  }

  void _cleanupFile(String path) {
    try {
      final file = File(path);
      file.exists().then((exists) {
        if (exists) file.delete();
      });
    } catch (_) {}
  }

  void dispose() {
    _warningTimer?.cancel();
    _amplitudeSubscription?.cancel();
    _recorder.dispose();
  }
}
