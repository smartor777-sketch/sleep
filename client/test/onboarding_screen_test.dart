import 'package:client/screens/onboarding_screen.dart';
import 'package:client/providers/profile_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'test_helpers.dart';

void main() {
  testWidgets('Onboarding save completes with entered text', (tester) async {
    var completed = false;
    String? savedAboutMe;
    bool? savedOnboarding;
    final profile = FakeProfileProvider(
      onSaveAboutMe: (String aboutMe, {bool? onboardingCompleted}) async {
        savedAboutMe = aboutMe;
        savedOnboarding = onboardingCompleted;
        return buildUser(
          aboutMe: aboutMe,
          onboardingCompleted: onboardingCompleted ?? false,
        );
      },
    );

    await tester.pumpWidget(
      ChangeNotifierProvider<ProfileProvider>.value(
        value: profile,
        child: MaterialApp(
          home: Scaffold(
            body: Stack(
              children: [
                const SizedBox.expand(),
                OnboardingScreen(onCompleted: () => completed = true),
              ],
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.byIcon(Icons.female_rounded));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Далее'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).at(0), 'Software developer');
    await tester.tap(find.text('Далее'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).at(0), 'Married, one child');
    await tester.tap(find.text('Далее'));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byType(TextField).at(0),
      'Psychology and hiking',
    );
    await tester.tap(find.text('Далее'));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byType(TextField).at(0),
      'Exploring a major life transition',
    );
    await tester.tap(find.text('Завершить'));
    await tester.pumpAndSettle();

    expect(savedAboutMe, contains('Женщина'));
    expect(savedAboutMe, contains('Software developer'));
    expect(savedAboutMe, contains('Married, one child'));
    expect(savedAboutMe, contains('Psychology and hiking'));
    expect(savedAboutMe, contains('Exploring a major life transition'));
    expect(savedAboutMe, isNot(contains('Gender:')));
    expect(savedAboutMe, contains(';'));
    expect(savedOnboarding, true);
    expect(completed, true);
  });

  testWidgets('Onboarding skip shows error toast on failure', (tester) async {
    final profile = FakeProfileProvider(
      onSaveAboutMe: (String aboutMe, {bool? onboardingCompleted}) async =>
          null,
    );

    await tester.pumpWidget(
      ChangeNotifierProvider<ProfileProvider>.value(
        value: profile,
        child: MaterialApp(
          home: Scaffold(
            body: Stack(
              children: [
                const SizedBox.expand(),
                OnboardingScreen(onCompleted: () {}),
              ],
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Пропустить'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Пропустить'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Пропустить'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Пропустить'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Пропустить'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.text('Не удалось завершить онбординг'), findsOneWidget);
  });

  testWidgets('Onboarding does not show back button and uses updated title', (
    tester,
  ) async {
    final profile = FakeProfileProvider(
      onSaveAboutMe: (String aboutMe, {bool? onboardingCompleted}) async {
        return buildUser(
          aboutMe: aboutMe,
          onboardingCompleted: onboardingCompleted ?? false,
        );
      },
    );

    await tester.pumpWidget(
      ChangeNotifierProvider<ProfileProvider>.value(
        value: profile,
        child: MaterialApp(
          home: Scaffold(
            body: Stack(
              children: [
                const SizedBox.expand(),
                OnboardingScreen(onCompleted: () {}),
              ],
            ),
          ),
        ),
      ),
    );

    expect(find.text('Давайте познакомимся'), findsOneWidget);
    expect(find.text('Назад'), findsNothing);
    expect(find.byIcon(Icons.female_rounded), findsOneWidget);
    expect(find.byIcon(Icons.male_rounded), findsOneWidget);
    expect(find.byIcon(Icons.question_mark_rounded), findsOneWidget);
    expect(find.byType(DropdownButtonFormField<String>), findsOneWidget);
  });
}
