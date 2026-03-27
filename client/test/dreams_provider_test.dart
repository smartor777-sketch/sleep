import 'package:client/providers/dreams_provider.dart';
import 'package:client/services/api_exception.dart';
import 'package:flutter_test/flutter_test.dart';

import 'test_helpers.dart';

void main() {
  test('loadDreams populates state on success', () async {
    final service = FakeDreamsService()
      ..onGetDreams = ({int page = 1, int pageSize = 50, String? date}) async {
        expect(page, 1);
        expect(pageSize, 50);
        expect(date, '2025-01-02');
        return [buildDream()];
      };
    final provider = DreamsProvider(FakeAuthProvider(), service: service);

    await provider.loadDreams(date: '2025-01-02');

    expect(provider.loading, false);
    expect(provider.error, isNull);
    expect(provider.dreams, hasLength(1));
    expect(provider.dreams.first.id, 'dream-1');
  });

  test('search surfaces api error state', () async {
    final service = FakeDreamsService()
      ..onSearchDreams = (String query, {String mode = 'semantic'}) async {
        expect(query, 'forest');
        expect(mode, 'semantic');
        throw ApiException(429, 'too_many_requests');
      };
    final provider = DreamsProvider(FakeAuthProvider(), service: service);

    await provider.search('forest');

    expect(provider.searching, false);
    expect(provider.error, 'too_many_requests');
    expect(provider.errorCode, 429);
  });

  test('createDream inserts dream with saved status and default gradient', () async {
    final created = buildDream(
      analysisStatus: 'saved',
      hasAnalysis: false,
      gradientColor1: '#FA9042',
      gradientColor2: '#8885FF',
    );
    final service = FakeDreamsService()
      ..onCreateDream = (String content) async {
        expect(content, 'new dream');
        return created;
      };
    final provider = DreamsProvider(FakeAuthProvider(), service: service);

    final dream = await provider.createDream('new dream');

    expect(dream, isNotNull);
    expect(provider.dreams.first.analysisStatus, 'saved');
    expect(provider.dreams.first.hasAnalysis, false);
  });

  test('triggerAnalysis starts polling until analyzed', () async {
    final initial = buildDream(analysisStatus: 'saved', hasAnalysis: false);
    final triggeredDream = initial.copyWith(analysisStatus: 'analyzing');
    final analyzedDream = initial.copyWith(
      hasAnalysis: true,
      analysisStatus: 'analyzed',
      gradientColor1: '#112233',
      gradientColor2: '#445566',
    );
    final refreshed = [triggeredDream, analyzedDream];
    var refreshIndex = 0;
    final service = FakeDreamsService();
    service.onGetDreams = ({int page = 1, int pageSize = 50, String? date}) async => [initial];
    service.onTriggerAnalysis = (String id) async {
      expect(id, initial.id);
      return triggeredDream;
    };
    service.onGetDream = (String id) async => refreshed[refreshIndex++];
    final provider = DreamsProvider(
      FakeAuthProvider(),
      service: service,
      pollInterval: Duration.zero,
      maxPollAttempts: 3,
    );
    await provider.loadDreams();

    final result = await provider.triggerAnalysis(initial.id);
    await Future<void>.delayed(Duration.zero);
    await Future<void>.delayed(Duration.zero);

    expect(result, isNotNull);
    expect(result!.analysisStatus, 'analyzing');
    expect(provider.dreams.first.analysisStatus, 'analyzed');
  });

  test('deleteDream removes item on success', () async {
    final initial = buildDream();
    final service = FakeDreamsService()
      ..onGetDreams = ({int page = 1, int pageSize = 50, String? date}) async {
        return [initial];
      }
      ..onDeleteDream = (String id) async {
        expect(id, initial.id);
      };
    final provider = DreamsProvider(FakeAuthProvider(), service: service);
    await provider.loadDreams();

    final result = await provider.deleteDream(initial.id);

    expect(result, true);
    expect(provider.dreams, isEmpty);
  });
}
