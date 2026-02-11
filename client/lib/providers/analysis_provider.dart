import 'package:flutter/material.dart';

import '../models/analysis_message.dart';
import '../models/dream.dart';
import '../services/analysis_service.dart';
import '../services/messages_service.dart';
import 'auth_provider.dart';
import '../services/api_exception.dart';

class AnalysisProvider extends ChangeNotifier {
  AnalysisProvider(this._auth) {
    _messagesService = MessagesService(_auth.apiClient);
    _analysisService = AnalysisService(_auth.apiClient);
  }

  final AuthProvider _auth;
  late final MessagesService _messagesService;
  late final AnalysisService _analysisService;

  final List<AnalysisMessage> _messages = [];
  bool _loading = false;
  bool _analysisInProgress = false;
  bool _analysisReady = false;
  bool _analysisStarted = false;
  Dream? _dream;
  String? _error;
  int? _errorCode;

  List<AnalysisMessage> get messages => List.unmodifiable(_messages);
  bool get loading => _loading;
  bool get analysisInProgress => _analysisInProgress;
  bool get analysisReady => _analysisReady;
  bool get analysisStarted => _analysisStarted;
  String? get error => _error;
  int? get errorCode => _errorCode;

  Future<void> load(Dream dream) async {
    _dream = dream;
    _loading = true;
    _error = null;
    _errorCode = null;
    _analysisStarted = false;
    _analysisInProgress = false;
    notifyListeners();
    try {
      await refreshMessages(dream.id);
      if (_analysisStarted && !_analysisReady) {
        _analysisInProgress = true;
        notifyListeners();
        await _pollMessages(dream.id);
        _analysisInProgress = false;
      }
    } catch (e) {
      if (e is ApiException) {
        _error = e.message;
        _errorCode = e.statusCode;
      } else {
        _error = 'network_error';
      }
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> refreshMessages(String dreamId) async {
    final items = await _messagesService.getMessages(dreamId);
    _messages
      ..clear()
      ..addAll(items);
    _analysisReady = _messages.any((m) => m.role == MessageRole.assistant);
    _analysisStarted = _messages.any((m) => m.role == MessageRole.user);
    notifyListeners();
  }

  bool get showDreamIntro {
    final dream = _dream;
    if (dream == null) return false;
    final content = dream.content.trim();
    if (content.isEmpty) return false;
    return !_messages.any((m) => m.role == MessageRole.user && m.content.trim() == content);
  }

  Future<void> startAnalysis() async {
    if (_dream == null || _analysisInProgress || _analysisReady) return;
    _analysisInProgress = true;
    _analysisStarted = true;
    _error = null;
    _errorCode = null;
    notifyListeners();
    try {
      final task = await _analysisService.createAnalysis(_dream!.id);
      await _pollAnalysis(task.taskId);
      await refreshMessages(_dream!.id);
    } catch (e) {
      if (e is ApiException) {
        _error = e.message;
        _errorCode = e.statusCode;
      } else {
        _error = 'network_error';
      }
    } finally {
      _analysisInProgress = false;
      notifyListeners();
    }
  }

  Future<void> sendMessage(String dreamId, String content) async {
    if (!_analysisReady) return;
    _loading = true;
    _error = null;
    _errorCode = null;
    notifyListeners();
    try {
      final result = await _messagesService.sendMessage(dreamId, content);
      _messages.add(result.userMessage);
      notifyListeners();
      await _pollMessageTask(result.taskId);
      await refreshMessages(dreamId);
    } catch (e) {
      if (e is ApiException) {
        _error = e.message;
        _errorCode = e.statusCode;
      } else {
        _error = 'network_error';
      }
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> _pollAnalysis(String taskId) async {
    for (var i = 0; i < 15; i++) {
      final status = await _analysisService.getTaskStatus(taskId);
      if (status.status == 'SUCCESS' || status.status == 'COMPLETED') {
        return;
      }
      if (status.status == 'FAILURE' || status.status == 'FAILED') {
        _error = 'analysis_failed';
        return;
      }
      await Future.delayed(const Duration(seconds: 2));
    }
  }

  Future<void> _pollMessages(String dreamId) async {
    for (var i = 0; i < 10; i++) {
      await refreshMessages(dreamId);
      if (_messages.isNotEmpty) return;
      await Future.delayed(const Duration(seconds: 2));
    }
  }

  Future<void> _pollMessageTask(String taskId) async {
    for (var i = 0; i < 15; i++) {
      final status = await _analysisService.getMessageTaskStatus(taskId);
      if (status.status == 'SUCCESS' || status.status == 'COMPLETED') {
        return;
      }
      if (status.status == 'FAILURE' || status.status == 'FAILED') {
        _error = 'message_failed';
        return;
      }
      await Future.delayed(const Duration(seconds: 2));
    }
  }

  void clearError() {
    _error = null;
    _errorCode = null;
    notifyListeners();
  }
}
