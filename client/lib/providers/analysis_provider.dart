import 'package:flutter/material.dart';

import '../models/analysis_message.dart';
import '../models/dream.dart';
import '../services/analysis_service.dart';
import '../services/messages_service.dart';
import 'auth_provider.dart';
import '../services/api_exception.dart';

class AnalysisProvider extends ChangeNotifier {
  AnalysisProvider(
    this._auth, {
    MessagesService? messagesService,
    AnalysisService? analysisService,
    Duration pollInterval = const Duration(seconds: 2),
    int maxAnalysisPollAttempts = 60,
    int maxMessagePollAttempts = 60,
    int maxInitialLoadPollAttempts = 30,
  })  : _pollInterval = pollInterval,
        _maxAnalysisPollAttempts = maxAnalysisPollAttempts,
        _maxMessagePollAttempts = maxMessagePollAttempts,
        _maxInitialLoadPollAttempts = maxInitialLoadPollAttempts {
    _messagesService = messagesService ?? MessagesService(_auth.apiClient);
    _analysisService = analysisService ?? AnalysisService(_auth.apiClient);
  }

  final AuthProvider _auth;
  final Duration _pollInterval;
  final int _maxAnalysisPollAttempts;
  final int _maxMessagePollAttempts;
  final int _maxInitialLoadPollAttempts;
  late final MessagesService _messagesService;
  late final AnalysisService _analysisService;

  final List<AnalysisMessage> _messages = [];
  bool _loading = false;
  bool _analysisInProgress = false;
  bool _analysisReady = false;
  bool _analysisStarted = false;
  bool _analysisFailed = false;
  Dream? _dream;
  String? _error;
  int? _errorCode;

  List<AnalysisMessage> get messages => List.unmodifiable(_messages);
  bool get loading => _loading;
  bool get analysisInProgress => _analysisInProgress;
  bool get analysisReady => _analysisReady;
  bool get analysisStarted => _analysisStarted;
  bool get analysisFailed => _analysisFailed;
  String? get error => _error;
  int? get errorCode => _errorCode;

  Future<void> load(Dream dream) async {
    _dream = dream;
    _loading = true;
    _error = null;
    _errorCode = null;
    _analysisStarted = false;
    _analysisInProgress = false;
    _analysisFailed = false;
    notifyListeners();
    try {
      await refreshMessages(dream.id);
      final snapshot = await _analysisService.getAnalysisByDream(dream.id);
      if (snapshot != null) {
        _analysisStarted = true;
        _analysisReady = snapshot.status == 'completed';
        _analysisInProgress =
            snapshot.status == 'pending' || snapshot.status == 'processing';
        _analysisFailed = snapshot.status == 'failed';
      }
      if ((_analysisStarted || _analysisInProgress) &&
          !_analysisReady &&
          !_analysisFailed) {
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
    if (_analysisReady) {
      _analysisFailed = false;
    }
    notifyListeners();
  }

  bool get showDreamIntro {
    final dream = _dream;
    if (dream == null) return false;
    final content = dream.content.trim();
    if (content.isEmpty) return false;
    return !_messages.any(
      (m) => m.role == MessageRole.user && m.content.trim() == content,
    );
  }

  Future<void> startAnalysis() async {
    if (_dream == null || _analysisInProgress || _analysisReady) return;
    _analysisInProgress = true;
    _analysisStarted = true;
    _analysisFailed = false;
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
    for (var i = 0; i < _maxAnalysisPollAttempts; i++) {
      final status = await _analysisService.getTaskStatus(taskId);
      if (status.status == 'SUCCESS' || status.status == 'COMPLETED') {
        return;
      }
      if (status.status == 'FAILURE' || status.status == 'FAILED') {
        _error = 'analysis_failed';
        _analysisFailed = true;
        return;
      }
      await Future.delayed(_pollInterval);
    }
  }

  Future<void> _pollMessages(String dreamId) async {
    for (var i = 0; i < _maxInitialLoadPollAttempts; i++) {
      await refreshMessages(dreamId);
      if (_analysisReady) return;
      final snapshot = await _analysisService.getAnalysisByDream(dreamId);
      if (snapshot?.status == 'failed') {
        _analysisFailed = true;
        return;
      }
      await Future.delayed(_pollInterval);
    }
  }

  Future<void> _pollMessageTask(String taskId) async {
    for (var i = 0; i < _maxMessagePollAttempts; i++) {
      final status = await _analysisService.getMessageTaskStatus(taskId);
      if (status.status == 'SUCCESS' || status.status == 'COMPLETED') {
        return;
      }
      if (status.status == 'FAILURE' || status.status == 'FAILED') {
        _error = 'message_failed';
        return;
      }
      await Future.delayed(_pollInterval);
    }
  }

  void clearError() {
    _error = null;
    _errorCode = null;
    notifyListeners();
  }
}
