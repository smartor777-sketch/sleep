import 'package:client/models/user_me.dart';
import 'package:client/providers/auth_provider.dart';
import 'package:client/providers/profile_provider.dart';
import 'package:client/services/api_exception.dart';
import 'package:client/services/auth_service.dart';
import 'package:client/services/stats_service.dart';
import 'package:client/services/users_service.dart';
import 'package:flutter_test/flutter_test.dart';

import 'test_helpers.dart';


class ProviderAuthService extends AuthService {
  ProviderAuthService() : super(FakeSecureStorageService());

  Future<UserMe> Function({required String deviceId})? onAnonymousAuth;

  @override
  Future<UserMe> anonymousAuth({required String deviceId}) {
    return onAnonymousAuth!(deviceId: deviceId);
  }
}


class ProviderStatsService extends StatsService {
  ProviderStatsService() : super(FakeApiClient());

  Future<Stats> Function()? onGetMyStats;

  @override
  Future<Stats> getMyStats() => onGetMyStats!();
}


class ProviderUsersService extends UsersService {
  ProviderUsersService() : super(FakeApiClient());

  Future<UserMe> Function({String? aboutMe, String? timezone, bool? onboardingCompleted})? onUpdateMe;

  @override
  Future<UserMe> updateMe({String? aboutMe, String? timezone, bool? onboardingCompleted}) {
    return onUpdateMe!(
      aboutMe: aboutMe,
      timezone: timezone,
      onboardingCompleted: onboardingCompleted,
    );
  }
}


void main() {
  test('AuthProvider bootstrap succeeds and updateUser notifies state', () async {
    final authService = ProviderAuthService()
      ..onAnonymousAuth = ({required String deviceId}) async {
        expect(deviceId, 'device-12345678');
        return buildUser(email: 'u@example.com', onboardingCompleted: true);
      };
    final provider = AuthProvider(
      authService: authService,
      apiClient: FakeApiClient(),
    );

    await provider.bootstrap();
    provider.updateUser(buildUser(id: 'user-2'));

    expect(provider.loading, false);
    expect(provider.error, isNull);
    expect(provider.user!.id, 'user-2');
  });

  test('AuthProvider bootstrap stores error on failure and ignores reentry', () async {
    final authService = ProviderAuthService()
      ..onAnonymousAuth = ({required String deviceId}) async {
        throw Exception('boom');
      };
    final provider = AuthProvider(
      authService: authService,
      apiClient: FakeApiClient(),
    );

    await Future.wait([provider.bootstrap(), provider.bootstrap()]);

    expect(provider.user, isNull);
    expect(provider.error, contains('boom'));
  });

  test('ProfileProvider loads stats and saves profile data', () async {
    final auth = FakeAuthProvider();
    auth.updateUser(buildUser(id: 'user-1'));
    final statsService = ProviderStatsService()
      ..onGetMyStats = () async => Stats(
            totalDreams: 2,
            streakDays: 1,
            dreamsByWeekday: const {'Mon': 1},
            dreamsLast14Days: [DayCount(date: '2025-01-02', count: 1)],
            archetypesTop: [ArchetypeCount(name: 'shadow', count: 2)],
            avgTimeOfDay: '06:30',
          );
    final usersService = ProviderUsersService()
      ..onUpdateMe = ({String? aboutMe, String? timezone, bool? onboardingCompleted}) async {
        return buildUser(
          id: 'user-1',
          aboutMe: aboutMe,
          onboardingCompleted: onboardingCompleted ?? false,
        );
      };
    final provider = ProfileProvider(
      auth,
      statsService: statsService,
      usersService: usersService,
    );

    await provider.loadStats();
    final updated = await provider.saveAboutMe('About', onboardingCompleted: true);

    expect(provider.stats!.totalDreams, 2);
    expect(updated!.aboutMe, 'About');
    expect(auth.user!.aboutMe, 'About');
  });

  test('ProfileProvider maps api and network errors', () async {
    final auth = FakeAuthProvider();
    final statsService = ProviderStatsService()
      ..onGetMyStats = () async => throw ApiException(400, 'bad_stats');
    final usersService = ProviderUsersService()
      ..onUpdateMe = ({String? aboutMe, String? timezone, bool? onboardingCompleted}) async {
        throw Exception('offline');
      };
    final provider = ProfileProvider(
      auth,
      statsService: statsService,
      usersService: usersService,
    );

    await provider.loadStats();
    expect(provider.error, 'bad_stats');

    provider.clearError();
    expect(provider.error, isNull);

    final updated = await provider.saveAboutMe('About');
    expect(updated, isNull);
    expect(provider.error, 'network_error');
  });
}
