import 'dart:convert';
import 'dart:io';

import 'package:client/models/analysis_message.dart';
import 'package:client/services/analysis_service.dart';
import 'package:client/services/api_client.dart';
import 'package:client/services/api_exception.dart';
import 'package:client/services/auth_service.dart';
import 'package:client/services/dreams_service.dart';
import 'package:client/services/messages_service.dart';
import 'package:client/services/secure_storage_service.dart';
import 'package:client/services/stats_service.dart';
import 'package:client/services/transcription_service.dart';
import 'package:client/services/users_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:uuid/uuid.dart';

import 'test_helpers.dart';

class MemoryStorage extends SecureStorageService {
  MemoryStorage({
    this.accessToken,
    this.refreshToken,
    this.deviceId = 'device-12345678',
  });

  String? accessToken;
  String? refreshToken;
  String deviceId;
  Color? accentColor;
  bool darkMode = false;

  @override
  Future<String?> getAccessToken() async => accessToken;

  @override
  Future<String?> getRefreshToken() async => refreshToken;

  @override
  Future<String> getOrCreateDeviceId() async => deviceId;

  @override
  Future<Color?> getAccentColor() async => accentColor;

  @override
  Future<bool> getDarkMode() async => darkMode;

  @override
  Future<void> setAccentColor(Color color) async {
    accentColor = color;
  }

  @override
  Future<void> setDarkMode(bool value) async {
    darkMode = value;
  }

  @override
  Future<void> setTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
  }
}

class FakeFlutterSecureStorage extends FlutterSecureStorage {
  FakeFlutterSecureStorage();

  final Map<String, String> values = {};

  @override
  Future<String?> read({
    required String key,
    AppleOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    AppleOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    return values[key];
  }

  @override
  Future<void> write({
    required String key,
    required String? value,
    AppleOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    AppleOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    if (value == null) {
      values.remove(key);
    } else {
      values[key] = value;
    }
  }
}

class FakeUuid extends Uuid {
  FakeUuid(this.value);

  final String value;

  @override
  String v4({Map<String, dynamic>? options, Object? config}) => value;
}

class MultipartAwareClient extends http.BaseClient {
  MultipartAwareClient({required this.handleRequest, required this.handleSend});

  final Future<http.Response> Function(http.Request request) handleRequest;
  final Future<http.StreamedResponse> Function(http.BaseRequest request)
  handleSend;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    if (request is http.Request) {
      final response = await handleRequest(request);
      return http.StreamedResponse(
        Stream.value(response.bodyBytes),
        response.statusCode,
        headers: response.headers,
        request: request,
      );
    }
    return handleSend(request);
  }
}

void main() {
  group('SecureStorageService', () {
    test('reads and writes all supported values', () async {
      final storage = FakeFlutterSecureStorage();
      final service = SecureStorageService(
        storage: storage,
        uuid: FakeUuid('uuid-1'),
      );

      expect(await service.getOrCreateDeviceId(), 'uuid-1');
      expect(await service.getOrCreateDeviceId(), 'uuid-1');

      await service.setTokens(accessToken: 'access', refreshToken: 'refresh');
      expect(await service.getAccessToken(), 'access');
      expect(await service.getRefreshToken(), 'refresh');

      expect(await service.getDarkMode(), false);
      await service.setDarkMode(true);
      expect(await service.getDarkMode(), true);

      expect(await service.getAccentColor(), isNull);
      await service.setAccentColor(const Color(0xFF112233));
      expect(
        (await service.getAccentColor())!.value,
        const Color(0xFF112233).value,
      );
    });
  });

  group('ApiClient', () {
    test('adds auth header and handles basic verbs', () async {
      final requests = <http.Request>[];
      final client = ApiClient(
        MemoryStorage(accessToken: 'token-1'),
        httpClient: MockClient((request) async {
          requests.add(request);
          return http.Response('{}', 200);
        }),
      );

      await client.get('/path');
      await client.post('/path', body: {'a': 1});
      await client.put('/path', body: {'b': 2});
      await client.patch('/path', body: {'c': 3});
      await client.delete('/path');

      expect(requests.map((r) => r.method).toList(), [
        'GET',
        'POST',
        'PUT',
        'PATCH',
        'DELETE',
      ]);
      expect(requests.first.headers['Authorization'], 'Bearer token-1');
      expect(requests[1].body, jsonEncode({'a': 1}));
    });

    test('skips auth header when auth is disabled', () async {
      http.Request? captured;
      final client = ApiClient(
        MemoryStorage(accessToken: 'token-1'),
        httpClient: MockClient((request) async {
          captured = request;
          return http.Response('{}', 200);
        }),
      );

      await client.get('/public', auth: false);

      expect(captured!.headers.containsKey('Authorization'), false);
    });

    test('refreshes token and retries after 401', () async {
      final storage = MemoryStorage(
        accessToken: 'old-access',
        refreshToken: 'refresh-1',
      );
      var count = 0;
      final client = ApiClient(
        storage,
        httpClient: MockClient((request) async {
          count += 1;
          if (count == 1) {
            expect(request.headers['Authorization'], 'Bearer old-access');
            return http.Response('{}', 401);
          }
          if (request.url.path.endsWith('/auth/refresh')) {
            return http.Response(
              jsonEncode({
                'access_token': 'new-access',
                'refresh_token': 'new-refresh',
              }),
              200,
            );
          }
          expect(request.headers['Authorization'], 'Bearer new-access');
          return http.Response('{"ok":true}', 200);
        }),
      );

      final response = await client.get('/needs-refresh');

      expect(response.statusCode, 200);
      expect(storage.accessToken, 'new-access');
      expect(storage.refreshToken, 'new-refresh');
    });

    test('returns original 401 when refresh is not possible', () async {
      final client = ApiClient(
        MemoryStorage(accessToken: 'old-access'),
        httpClient: MockClient((request) async => http.Response('{}', 401)),
      );

      final response = await client.get('/needs-refresh');

      expect(response.statusCode, 401);
    });

    test('retries multipart request after refresh', () async {
      final storage = MemoryStorage(
        accessToken: 'old-access',
        refreshToken: 'refresh-1',
      );
      final requests = <http.BaseRequest>[];
      var uploadCount = 0;
      final client = ApiClient(
        storage,
        httpClient: MultipartAwareClient(
          handleRequest: (request) async {
            if (request.url.path.endsWith('/auth/refresh')) {
              return http.Response(
                jsonEncode({
                  'access_token': 'new-access',
                  'refresh_token': 'new-refresh',
                }),
                200,
              );
            }
            return http.Response('{}', 200);
          },
          handleSend: (request) async {
            requests.add(request);
            uploadCount += 1;
            final status = uploadCount == 1 ? 401 : 200;
            return http.StreamedResponse(
              Stream.value(utf8.encode('{"text":"ok"}')),
              status,
              request: request,
            );
          },
        ),
      );

      final tempDir = await Directory.systemTemp.createTemp('multipart-test');
      final file = File('${tempDir.path}/audio.m4a')
        ..writeAsBytesSync([1, 2, 3]);

      final response = await client.postMultipart(
        '/api/v1/audio/transcriptions',
        fileField: 'file',
        filePath: file.path,
        fields: {'language': 'ru'},
      );
      final body = await response.stream.bytesToString();

      expect(body, contains('"text":"ok"'));
      expect(requests, hasLength(2));
      expect(requests.first.headers['Authorization'], 'Bearer old-access');
      expect(requests.last.headers['Authorization'], 'Bearer new-access');
      await tempDir.delete(recursive: true);
    });
  });

  group('DreamsService', () {
    test('covers list/search/create/get/update/delete flows', () async {
      final client = FakeApiClient();
      final responses = <String, http.Response>{
        'GET:/api/v1/dreams?page=1&page_size=50&date=2025-01-02': http.Response(
          jsonEncode({
            'dreams': [
              {
                'id': 'dream-1',
                'user_id': 'user-1',
                'title': 'Title',
                'content': 'Body',
                'recorded_at': '2025-01-02T03:04:05Z',
                'created_at': '2025-01-02T03:04:05Z',
                'updated_at': '2025-01-02T03:04:05Z',
              },
            ],
          }),
          200,
        ),
        'GET:/api/v1/dreams/search?q=forest&mode=semantic': http.Response(
          jsonEncode({
            'dreams': [
              {
                'id': 'dream-2',
                'user_id': 'user-1',
                'title': 'Search',
                'content': 'Forest',
                'recorded_at': '2025-01-02T03:04:05Z',
                'created_at': '2025-01-02T03:04:05Z',
                'updated_at': '2025-01-02T03:04:05Z',
              },
            ],
          }),
          200,
        ),
        'GET:/api/v1/dreams/dream-1': http.Response(
          jsonEncode({
            'id': 'dream-1',
            'user_id': 'user-1',
            'title': 'Title',
            'content': 'Body',
            'recorded_at': '2025-01-02T03:04:05Z',
            'created_at': '2025-01-02T03:04:05Z',
            'updated_at': '2025-01-02T03:04:05Z',
          }),
          200,
        ),
      };

      client.onGet = (path, {auth = true}) async =>
          responses['GET:$path'] ?? http.Response('{}', 200);
      client.onPost = (path, {body, auth = true}) async {
        final data = body! as Map<String, dynamic>;
        return http.Response(
          jsonEncode({
            'id': 'dream-3',
            'user_id': 'user-1',
            'title': null,
            'content': data['content'],
            'recorded_at': '2025-01-02T03:04:05Z',
            'created_at': '2025-01-02T03:04:05Z',
            'updated_at': '2025-01-02T03:04:05Z',
          }),
          path == '/api/v1/dreams' ? 201 : 200,
        );
      };
      client.onPut = (path, {body, auth = true}) async {
        final data = body! as Map<String, dynamic>;
        return http.Response(
          jsonEncode({
            'id': 'dream-3',
            'user_id': 'user-1',
            'title': data['title'],
            'content': data['content'] ?? 'Updated',
            'recorded_at': '2025-01-02T03:04:05Z',
            'created_at': '2025-01-02T03:04:05Z',
            'updated_at': '2025-01-02T03:04:05Z',
          }),
          200,
        );
      };
      client.onPatch = (path, {body, auth = true}) async {
        final data = body! as Map<String, dynamic>;
        return http.Response(
          jsonEncode({
            'id': 'dream-3',
            'user_id': 'user-1',
            'title': 'Updated',
            'content': 'Updated',
            'recorded_at': data['created_at'],
            'created_at': data['created_at'],
            'updated_at': '2025-01-02T03:04:05Z',
          }),
          200,
        );
      };
      client.onDelete = (path, {auth = true}) async => http.Response('{}', 204);

      final service = DreamsService(client);
      expect(
        (await service.getDreams(date: '2025-01-02')).single.id,
        'dream-1',
      );
      expect((await service.searchDreams('forest')).single.id, 'dream-2');
      expect((await service.createDream('New dream')).content, 'New dream');
      expect((await service.getDream('dream-1')).analysisStatus, 'saved');
      expect(
        (await service.updateDream('dream-3', 'Updated')).content,
        'Updated',
      );
      expect(
        (await service.updateDreamTitle('dream-3', 'New title')).title,
        'New title',
      );
      expect(
        (await service.updateDreamDate(
          'dream-3',
          DateTime.utc(2025, 1, 2),
        )).createdAt,
        DateTime.parse('2025-01-02T00:00:00.000Z'),
      );
      await service.deleteDream('dream-3');
    });

    test('throws ApiException for non-2xx responses', () async {
      final client = FakeApiClient();
      client.onGet = (path, {auth = true}) async =>
          http.Response('{"detail":"bad"}', 400);
      client.onPost = (path, {body, auth = true}) async =>
          http.Response('{"detail":"bad"}', 400);
      final service = DreamsService(client);

      expect(() => service.getDream('id'), throwsA(isA<ApiException>()));
      expect(() => service.createDream('x'), throwsA(isA<ApiException>()));
    });
  });

  group('TranscriptionService', () {
    test('uploads audio and returns transcription text', () async {
      final client = FakeApiClient()
        ..onPostMultipart =
            (
              String path, {
              required String fileField,
              required String filePath,
              Map<String, String>? fields,
              bool auth = true,
            }) async {
              expect(path, '/api/v1/audio/transcriptions');
              expect(fileField, 'file');
              expect(filePath, '/tmp/audio.m4a');
              expect(fields, {'language': 'ru'});
              return http.StreamedResponse(
                Stream.value(utf8.encode('{"text":"dream text"}')),
                200,
              );
            };

      final service = TranscriptionService(client);
      final text = await service.transcribeAudioFile(
        '/tmp/audio.m4a',
        language: 'ru',
      );

      expect(text.text, 'dream text');
    });

    test('throws ApiException for backend errors', () async {
      final client = FakeApiClient()
        ..onPostMultipart =
            (
              String path, {
              required String fileField,
              required String filePath,
              Map<String, String>? fields,
              bool auth = true,
            }) async {
              return http.StreamedResponse(
                Stream.value(utf8.encode('{"detail":"bad audio"}')),
                400,
              );
            };

      final service = TranscriptionService(client);

      expect(
        () => service.transcribeAudioFile('/tmp/audio.m4a'),
        throwsA(
          isA<ApiException>().having((e) => e.message, 'message', 'bad audio'),
        ),
      );
    });
  });

  group('Analysis and message services', () {
    test('map success and error responses', () async {
      final client = FakeApiClient();
      client.onPost = (path, {body, auth = true}) async {
        if (path == '/api/v1/analyses') {
          return http.Response(
            '{"analysis_id":"a1","task_id":"t1","status":"pending"}',
            202,
          );
        }
        return http.Response(
          jsonEncode({
            'task_id': 'mt1',
            'status': 'processing',
            'user_message': {
              'id': 'm1',
              'dream_id': 'd1',
              'content': 'hello',
              'role': 'user',
              'created_at': '2025-01-02T03:04:05Z',
            },
          }),
          202,
        );
      };
      client.onGet = (path, {auth = true}) async {
        if (path == '/api/v1/analyses/task/t1') {
          return http.Response(
            '{"status":"SUCCESS","result":"ok","error":null}',
            200,
          );
        }
        if (path == '/api/v1/analyses/dream/missing') {
          return http.Response('{}', 404);
        }
        if (path == '/api/v1/analyses/dream/d1') {
          return http.Response(
            '{"status":"completed","result":"done","error_message":null}',
            200,
          );
        }
        if (path == '/api/v1/messages/task/mt1') {
          return http.Response('{"status":"SUCCESS","result":"reply"}', 200);
        }
        return http.Response(
          jsonEncode({
            'messages': [
              {
                'id': 'm1',
                'dream_id': 'd1',
                'content': 'hello',
                'role': 'user',
                'created_at': '2025-01-02T03:04:05Z',
              },
            ],
          }),
          200,
        );
      };

      final analysis = AnalysisService(client);
      final messages = MessagesService(client);

      expect((await analysis.createAnalysis('d1')).taskId, 't1');
      expect((await analysis.getTaskStatus('t1')).result, 'ok');
      expect(await analysis.getAnalysisByDream('missing'), isNull);
      expect((await analysis.getAnalysisByDream('d1'))!.status, 'completed');
      expect((await analysis.getMessageTaskStatus('mt1')).status, 'SUCCESS');
      expect((await messages.getMessages('d1')).single.role, MessageRole.user);
      expect((await messages.sendMessage('d1', 'hello')).taskId, 'mt1');
    });

    test('throw ApiException for bad analysis/message responses', () async {
      final client = FakeApiClient();
      client.onPost = (path, {body, auth = true}) async =>
          http.Response('{"detail":"bad"}', 400);
      client.onGet = (path, {auth = true}) async =>
          http.Response('{"detail":"bad"}', 400);
      final analysis = AnalysisService(client);
      final messages = MessagesService(client);

      expect(() => analysis.createAnalysis('d1'), throwsA(isA<ApiException>()));
      expect(() => analysis.getTaskStatus('t1'), throwsA(isA<ApiException>()));
      expect(
        () => analysis.getAnalysisByDream('d1'),
        throwsA(isA<ApiException>()),
      );
      expect(
        () => analysis.getMessageTaskStatus('mt1'),
        throwsA(isA<ApiException>()),
      );
      expect(() => messages.getMessages('d1'), throwsA(isA<ApiException>()));
      expect(
        () => messages.sendMessage('d1', 'hello'),
        throwsA(isA<ApiException>()),
      );
    });
  });

  group('Auth, stats and users services', () {
    test('AuthService anonymousAuth, getMe and linkProvider flows', () async {
      final storage = MemoryStorage();
      final api = FakeApiClient();
      api.onGet = (path, {auth = true}) async => http.Response(
        jsonEncode({
          'id': 'user-1',
          'email': 'u@example.com',
          'is_anonymous': false,
          'linked_providers': ['google'],
          'profile': {'about_me': 'About', 'onboarding_completed': true},
        }),
        200,
      );
      api.onPost = (path, {body, auth = true}) async {
        if (path == '/api/v1/auth/link') {
          return http.Response('{}', 200);
        }
        return http.Response('{}', 500);
      };
      final httpClient = MockClient((request) async {
        return http.Response(
          jsonEncode({'access_token': 'access', 'refresh_token': 'refresh'}),
          200,
        );
      });
      final service = AuthService(
        storage,
        apiClient: api,
        httpClient: httpClient,
      );

      final user = await service.anonymousAuth(deviceId: 'device-1');
      expect(storage.accessToken, 'access');
      expect(user.linkedProviders, ['google']);
      expect((await service.getMe()).aboutMe, 'About');
      expect(
        (await service.linkProvider(provider: 'google', idToken: 'token')).id,
        'user-1',
      );
    });

    test('AuthService throws on invalid responses', () async {
      final storage = MemoryStorage();
      final api = FakeApiClient();
      api.onGet = (path, {auth = true}) async => http.Response('{}', 500);
      api.onPost = (path, {body, auth = true}) async =>
          http.Response('{}', 409);
      final badHttp = MockClient((request) async => http.Response('{}', 500));
      final invalidHttp = MockClient(
        (request) async => http.Response('{"access_token":"a"}', 200),
      );
      final service = AuthService(storage, apiClient: api, httpClient: badHttp);
      final invalidService = AuthService(
        storage,
        apiClient: api,
        httpClient: invalidHttp,
      );

      expect(
        () => service.anonymousAuth(deviceId: 'device-1'),
        throwsException,
      );
      expect(
        () => invalidService.anonymousAuth(deviceId: 'device-1'),
        throwsException,
      );
      expect(() => service.getMe(), throwsException);
      expect(
        () => service.linkProvider(provider: 'google', idToken: 'token'),
        throwsException,
      );
    });

    test('StatsService and UsersService map success and errors', () async {
      final client = FakeApiClient();
      client.onGet = (path, {auth = true}) async => http.Response(
        jsonEncode({
          'total_dreams': 2,
          'streak_days': 1,
          'dreams_by_weekday': {'Mon': 1},
          'dreams_last_14_days': [
            {'date': '2025-01-02', 'count': 1},
          ],
          'archetypes_top': [
            {'name': 'shadow', 'count': 2},
          ],
          'avg_time_of_day': '06:30',
        }),
        200,
      );
      client.onPut = (path, {body, auth = true}) async {
        final data = body! as Map<String, dynamic>;
        return http.Response(
          jsonEncode({
            'id': 'user-1',
            'email': null,
            'is_anonymous': true,
            'linked_providers': [],
            'profile': {
              'about_me': data['self_description'],
              'onboarding_completed': data['onboarding_completed'],
            },
          }),
          200,
        );
      };

      final stats = await StatsService(client).getMyStats();
      final user = await UsersService(
        client,
      ).updateMe(aboutMe: 'About', timezone: 'UTC', onboardingCompleted: true);

      expect(stats.totalDreams, 2);
      expect(stats.dreamsLast14Days.single.count, 1);
      expect(stats.archetypesTop.single.name, 'shadow');
      expect(user.aboutMe, 'About');
      expect(user.onboardingCompleted, true);

      client.onGet = (path, {auth = true}) async =>
          http.Response('{"detail":"bad"}', 400);
      client.onPut = (path, {body, auth = true}) async =>
          http.Response('{"detail":"bad"}', 400);

      expect(
        () => StatsService(client).getMyStats(),
        throwsA(isA<ApiException>()),
      );
      expect(
        () => UsersService(client).updateMe(aboutMe: 'x'),
        throwsA(isA<ApiException>()),
      );
    });
  });
}
