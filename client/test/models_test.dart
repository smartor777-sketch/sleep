import 'package:client/models/analysis_message.dart';
import 'package:client/models/dream.dart';
import 'package:client/models/user_me.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Dream.fromJson and copyWith map backend fields', () {
    final dream = Dream.fromJson({
      'id': 'dream-1',
      'user_id': 'user-1',
      'title': 'Forest House',
      'content': 'A detailed dream',
      'emoji': null,
      'comment': null,
      'recorded_at': '2025-01-02T03:04:05Z',
      'created_at': '2025-01-02T03:04:05Z',
      'updated_at': '2025-01-02T03:04:05Z',
      'has_analysis': true,
      'analysis_status': 'analyzed',
      'analysis_error_message': null,
      'gradient_color_1': '#112233',
      'gradient_color_2': '#445566',
    });

    final updated = dream.copyWith(title: 'Updated', analysisStatus: 'analysis_failed');

    expect(dream.emoji, '');
    expect(dream.comment, '');
    expect(dream.hasAnalysis, true);
    expect(updated.title, 'Updated');
    expect(updated.analysisStatus, 'analysis_failed');
  });

  test('AnalysisMessage maps role and serializes back to json', () {
    final message = AnalysisMessage.fromJson({
      'id': 'msg-1',
      'dream_id': 'dream-1',
      'content': 'hello',
      'role': 'user',
      'created_at': '2025-01-02T03:04:05Z',
    });
    final unknown = AnalysisMessage.fromJson({
      'id': 'msg-2',
      'content': 'fallback',
      'role': 'unknown',
      'created_at': '2025-01-02T03:04:05Z',
    });

    expect(message.role, MessageRole.user);
    expect(unknown.role, MessageRole.assistant);
    expect(message.toJson()['role'], 'user');
  });

  test('UserMe.fromJson reads profile fields and defaults', () {
    final user = UserMe.fromJson({
      'id': 'user-1',
      'email': 'u@example.com',
      'is_anonymous': false,
      'linked_providers': ['google'],
      'profile': {
        'about_me': 'About',
        'onboarding_completed': true,
      },
    });
    final fallback = UserMe.fromJson({
      'id': 'user-2',
    });

    expect(user.aboutMe, 'About');
    expect(user.onboardingCompleted, true);
    expect(fallback.isAnonymous, true);
    expect(fallback.linkedProviders, isEmpty);
  });
}
