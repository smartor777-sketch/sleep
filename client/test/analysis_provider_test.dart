import 'package:client/providers/analysis_provider.dart';
import 'package:client/models/analysis_message.dart';
import 'package:client/services/analysis_service.dart';
import 'package:client/services/messages_service.dart';
import 'package:flutter_test/flutter_test.dart';

import 'test_helpers.dart';

void main() {
  test('load marks analysis ready after polling messages', () async {
    var messagesCall = 0;
    final messages = FakeMessagesService()
      ..onGetMessages = (String dreamId, {int limit = 200, int offset = 0}) async {
        messagesCall += 1;
        if (messagesCall == 1) return [];
        return [
          buildMessage(
            role: MessageRole.assistant,
            content: 'analysis text',
            dreamId: dreamId,
          ),
        ];
      };
    final analysis = FakeAnalysisService()
      ..onGetAnalysisByDream = (String dreamId) async {
        return AnalysisStatusSnapshot(status: 'pending', result: null, errorMessage: null);
      }
      ..onGetTaskStatus = (String taskId) async {
        throw UnimplementedError();
      }
      ..onGetMessageTaskStatus = (String taskId) async {
        throw UnimplementedError();
      };
    final provider = AnalysisProvider(
      FakeAuthProvider(),
      messagesService: messages,
      analysisService: analysis,
      pollInterval: Duration.zero,
      maxInitialLoadPollAttempts: 3,
    );

    await provider.load(buildDream(id: 'dream-load'));

    expect(provider.analysisReady, true);
    expect(provider.analysisInProgress, false);
    expect(provider.messages, hasLength(1));
  });

  test('startAnalysis completes and refreshes messages', () async {
    final messages = FakeMessagesService()
      ..onGetMessages = (String dreamId, {int limit = 200, int offset = 0}) async {
        return [
          buildMessage(
            role: MessageRole.assistant,
            content: 'done',
            dreamId: dreamId,
          ),
        ];
      }
      ..onSendMessage = (String dreamId, String content) async {
        throw UnimplementedError();
      };
    var taskCalls = 0;
    final analysis = FakeAnalysisService()
      ..onGetAnalysisByDream = (String dreamId) async {
        return null;
      }
      ..onCreateAnalysis = (String dreamId) async {
        return AnalysisTask(
          analysisId: 'analysis-1',
          taskId: 'task-1',
          status: 'pending',
        );
      }
      ..onGetTaskStatus = (String taskId) async {
        taskCalls += 1;
        return TaskStatus(status: taskCalls == 1 ? 'PENDING' : 'SUCCESS');
      }
      ..onGetMessageTaskStatus = (String taskId) async {
        throw UnimplementedError();
      };
    final provider = AnalysisProvider(
      FakeAuthProvider(),
      messagesService: messages,
      analysisService: analysis,
      pollInterval: Duration.zero,
      maxAnalysisPollAttempts: 3,
    );
    await provider.load(buildDream(id: 'dream-start'));

    await provider.startAnalysis();

    expect(provider.analysisReady, true);
    expect(provider.analysisInProgress, false);
    expect(provider.error, isNull);
    expect(provider.messages, hasLength(1));
  });

  test('sendMessage sets failure error state when reply task fails', () async {
    final userMessage = buildMessage(
      id: 'msg-user',
      role: MessageRole.user,
      content: 'follow up',
    );
    final messages = FakeMessagesService()
      ..onGetMessages = (String dreamId, {int limit = 200, int offset = 0}) async {
        return [
          buildMessage(
            id: 'msg-assistant',
            role: MessageRole.assistant,
            content: 'ready',
            dreamId: dreamId,
          ),
        ];
      }
      ..onSendMessage = (String dreamId, String content) async {
        return SendMessageResult(
          taskId: 'msg-task-1',
          status: 'processing',
          userMessage: userMessage,
        );
      };
    final analysis = FakeAnalysisService()
      ..onGetAnalysisByDream = (String dreamId) async {
        return AnalysisStatusSnapshot(status: 'completed', result: 'ready', errorMessage: null);
      }
      ..onCreateAnalysis = (String dreamId) async {
        throw UnimplementedError();
      }
      ..onGetTaskStatus = (String taskId) async {
        throw UnimplementedError();
      }
      ..onGetMessageTaskStatus = (String taskId) async {
        return MessageTaskStatus(status: 'FAILURE', error: 'boom');
      };
    final provider = AnalysisProvider(
      FakeAuthProvider(),
      messagesService: messages,
      analysisService: analysis,
      pollInterval: Duration.zero,
      maxMessagePollAttempts: 2,
    );
    await provider.load(buildDream(id: 'dream-send', hasAnalysis: true, analysisStatus: 'analyzed'));

    await provider.sendMessage('dream-send', 'follow up');

    expect(provider.error, 'message_failed');
    expect(provider.messages.any((m) => m.id == 'msg-assistant'), true);
  });
}
