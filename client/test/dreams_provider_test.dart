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

  test('createDream inserts and polls until analyzed', () async {
    final created = buildDream(
      analysisStatus: 'analyzing',
      hasAnalysis: false,
    );
    final refreshed = [
      created,
      created.copyWith(
        hasAnalysis: true,
        analysisStatus: 'analyzed',
        gradientColor1: '#112233',
        gradientColor2: '#445566',
      ),
    ];
    var refreshIndex = 0;
    final service = FakeDreamsService()
      ..onCreateDream = (String content) async {
        expect(content, 'new dream');
        return created;
      }
      ..onGetDream = (String id) async => refreshed[refreshIndex++];
    final provider = DreamsProvider(
      FakeAuthProvider(),
      service: service,
      pollInterval: Duration.zero,
      maxPollAttempts: 3,
    );

    final dream = await provider.createDream('new dream');
    await Future<void>.delayed(Duration.zero);
    await Future<void>.delayed(Duration.zero);

    expect(dream, isNotNull);
    expect(provider.dreams.first.analysisStatus, 'analyzed');
    expect(provider.dreams.first.hasAnalysis, true);
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
