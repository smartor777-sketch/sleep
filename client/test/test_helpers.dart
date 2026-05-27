import 'package:client/models/analysis_message.dart';
import 'package:client/models/dream.dart';
import 'package:client/models/user_me.dart';
import 'package:client/providers/auth_provider.dart';
import 'package:client/providers/profile_provider.dart';
import 'package:client/services/analysis_service.dart';
import 'package:client/services/api_client.dart';
import 'package:client/services/auth_service.dart';
import 'package:client/services/dreams_service.dart';
import 'package:client/services/messages_service.dart';
import 'package:client/services/secure_storage_service.dart';
import 'package:client/services/stats_service.dart';
import 'package:client/services/transcription_service.dart';
import 'package:client/services/users_service.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class FakeSecureStorageService extends SecureStorageService {
  final Map<String, String> _tokens = {};
  final String _deviceId = 'device-12345678';

  @override
  Future<String> getOrCreateDeviceId() async => _deviceId;

  @override
  Future<String?> getAccessToken() async => _tokens['access'];

  @override
  Future<String?> getRefreshToken() async => _tokens['refresh'];

  @override
  Future<void> setTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    _tokens['access'] = accessToken;
    _tokens['refresh'] = refreshToken;
  }
}

class FakeApiClient extends ApiClient {
  FakeApiClient() : super(FakeSecureStorageService());

  Future<http.Response> Function(String path, {bool auth})? onGet;
  Future<http.Response> Function(String path, {Object? body, bool auth})?
  onPost;
  Future<http.Response> Function(String path, {Object? body, bool auth})? onPut;
  Future<http.Response> Function(String path, {Object? body, bool auth})?
  onPatch;
  Future<http.Response> Function(String path, {bool auth})? onDelete;
  Future<http.StreamedResponse> Function(
    String path, {
    required String fileField,
    required String filePath,
    Map<String, String>? fields,
    bool auth,
  })?
  onPostMultipart;

  @override
  Future<http.Response> delete(String path, {bool auth = true}) =>
      onDelete!(path, auth: auth);

  @override
  Future<http.Response> get(String path, {bool auth = true}) =>
      onGet!(path, auth: auth);

  @override
  Future<http.Response> patch(String path, {Object? body, bool auth = true}) =>
      onPatch!(path, body: body, auth: auth);

  @override
  Future<http.Response> post(String path, {Object? body, bool auth = true}) =>
      onPost!(path, body: body, auth: auth);

  @override
  Future<http.StreamedResponse> postMultipart(
    String path, {
    required String fileField,
    required String filePath,
    Map<String, String>? fields,
    bool auth = true,
  }) {
    return onPostMultipart!(
      path,
      fileField: fileField,
      filePath: filePath,
      fields: fields,
      auth: auth,
    );
  }

  @override
  Future<http.Response> put(String path, {Object? body, bool auth = true}) =>
      onPut!(path, body: body, auth: auth);
}

class FakeAuthService extends AuthService {
  FakeAuthService() : super(FakeSecureStorageService());
}

class FakeAuthProvider extends AuthProvider {
  FakeAuthProvider()
    : super(authService: FakeAuthService(), apiClient: FakeApiClient());
}

class FakeDreamsService extends DreamsService {
  FakeDreamsService() : super(FakeApiClient());

  Future<List<Dream>> Function({int page, int pageSize, String? date})?
  onGetDreams;
  Future<List<Dream>> Function(String query, {String mode})? onSearchDreams;
  Future<Dream> Function(String content)? onCreateDream;
  Future<Dream> Function(String id)? onGetDream;
  Future<Dream> Function(String id, String content)? onUpdateDream;
  Future<Dream> Function(String id, String? title)? onUpdateDreamTitle;
  Future<Dream> Function(String id, DateTime createdAt)? onUpdateDreamDate;
  Future<void> Function(String id)? onDeleteDream;

  @override
  Future<Dream> createDream(String content) => onCreateDream!(content);

  @override
  Future<void> deleteDream(String id) => onDeleteDream!(id);

  @override
  Future<Dream> getDream(String id) => onGetDream!(id);

  @override
  Future<List<Dream>> getDreams({
    int page = 1,
    int pageSize = 50,
    String? date,
  }) {
    return onGetDreams!(page: page, pageSize: pageSize, date: date);
  }

  @override
  Future<List<Dream>> searchDreams(String query, {String mode = 'semantic'}) {
    return onSearchDreams!(query, mode: mode);
  }

  @override
  Future<Dream> updateDream(String id, String content) =>
      onUpdateDream!(id, content);

  @override
  Future<Dream> updateDreamDate(String id, DateTime createdAt) {
    return onUpdateDreamDate!(id, createdAt);
  }

  @override
  Future<Dream> updateDreamTitle(String id, String? title) {
    return onUpdateDreamTitle!(id, title);
  }
}

class FakeAnalysisService extends AnalysisService {
  FakeAnalysisService() : super(FakeApiClient());

  Future<AnalysisTask> Function(String dreamId)? onCreateAnalysis;
  Future<AnalysisStatusSnapshot?> Function(String dreamId)?
  onGetAnalysisByDream;
  Future<MessageTaskStatus> Function(String taskId)? onGetMessageTaskStatus;
  Future<TaskStatus> Function(String taskId)? onGetTaskStatus;

  @override
  Future<AnalysisTask> createAnalysis(String dreamId) =>
      onCreateAnalysis!(dreamId);

  @override
  Future<AnalysisStatusSnapshot?> getAnalysisByDream(String dreamId) {
    return onGetAnalysisByDream!(dreamId);
  }

  @override
  Future<MessageTaskStatus> getMessageTaskStatus(String taskId) {
    return onGetMessageTaskStatus!(taskId);
  }

  @override
  Future<TaskStatus> getTaskStatus(String taskId) => onGetTaskStatus!(taskId);
}

class FakeMessagesService extends MessagesService {
  FakeMessagesService() : super(FakeApiClient());

  Future<List<AnalysisMessage>> Function(
    String dreamId, {
    int limit,
    int offset,
  })?
  onGetMessages;
  Future<SendMessageResult> Function(String dreamId, String content)?
  onSendMessage;

  @override
  Future<List<AnalysisMessage>> getMessages(
    String dreamId, {
    int limit = 200,
    int offset = 0,
  }) {
    return onGetMessages!(dreamId, limit: limit, offset: offset);
  }

  @override
  Future<SendMessageResult> sendMessage(String dreamId, String content) {
    return onSendMessage!(dreamId, content);
  }
}

class FakeStatsService extends StatsService {
  FakeStatsService() : super(FakeApiClient());
}

class FakeUsersService extends UsersService {
  FakeUsersService() : super(FakeApiClient());
}

class FakeTranscriptionService extends TranscriptionService {
  FakeTranscriptionService() : super(FakeApiClient());

  Future<TranscriptionResult> Function(String filePath, {String? language, String? prompt})?
  onTranscribeAudioFile;

  @override
  Future<TranscriptionResult> transcribeAudioFile(
    String filePath, {
    String? language,
    String? prompt,
  }) {
    return onTranscribeAudioFile!(filePath, language: language, prompt: prompt);
  }
}

class FakeProfileProvider extends ProfileProvider {
  FakeProfileProvider({this.onSaveAboutMe})
    : super(
        FakeAuthProvider(),
        statsService: FakeStatsService(),
        usersService: FakeUsersService(),
      );

  final Future<UserMe?> Function(String aboutMe, {bool? onboardingCompleted})?
  onSaveAboutMe;

  @override
  Future<UserMe?> saveAboutMe(String aboutMe, {bool? onboardingCompleted}) {
    return onSaveAboutMe!(aboutMe, onboardingCompleted: onboardingCompleted);
  }
}

Dream buildDream({
  String id = 'dream-1',
  String? title = 'Forest House',
  String content = 'I walked into a forest house.',
  bool hasAnalysis = false,
  String analysisStatus = 'saved',
  String? analysisErrorMessage,
  String? gradientColor1,
  String? gradientColor2,
}) {
  final now = DateTime.utc(2025, 1, 2, 3, 4, 5);
  return Dream(
    id: id,
    userId: 'user-1',
    title: title,
    content: content,
    emoji: '',
    comment: '',
    recordedAt: now,
    createdAt: now,
    updatedAt: now,
    hasAnalysis: hasAnalysis,
    analysisStatus: analysisStatus,
    analysisErrorMessage: analysisErrorMessage,
    gradientColor1: gradientColor1,
    gradientColor2: gradientColor2,
  );
}

AnalysisMessage buildMessage({
  String id = 'msg-1',
  String content = 'Hello',
  MessageRole role = MessageRole.user,
  String? dreamId = 'dream-1',
}) {
  return AnalysisMessage(
    id: id,
    dreamId: dreamId,
    content: content,
    role: role,
    createdAt: DateTime.utc(2025, 1, 2, 3, 4, 5),
  );
}

UserMe buildUser({
  String id = 'user-1',
  String? email,
  bool isAnonymous = true,
  List<String> linkedProviders = const [],
  String? aboutMe,
  bool onboardingCompleted = false,
}) {
  return UserMe(
    id: id,
    email: email,
    isAnonymous: isAnonymous,
    linkedProviders: linkedProviders,
    aboutMe: aboutMe,
    onboardingCompleted: onboardingCompleted,
  );
}

Widget wrapWithMaterial(Widget child) {
  return MaterialApp(home: Scaffold(body: child));
}
