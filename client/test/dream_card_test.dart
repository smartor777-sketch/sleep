import 'package:client/widgets/dream_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'test_helpers.dart';

void main() {
  testWidgets('DreamCard renders gradient title and date', (tester) async {
    await tester.pumpWidget(
      wrapWithMaterial(
        SizedBox(
          width: 180,
          height: 180,
          child: DreamCard(
            dream: buildDream(
              hasAnalysis: true,
              analysisStatus: 'analyzed',
              gradientColor1: '#112233',
              gradientColor2: '#445566',
            ),
            accentColor: Colors.orange,
          ),
        ),
      ),
    );

    expect(find.text('Forest House'), findsOneWidget);
    expect(find.text('02.01.2025'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(find.byIcon(Icons.error_outline), findsNothing);

    final titleWidget = tester.widget<Text>(find.text('Forest House'));
    expect(titleWidget.style?.fontSize, 12);
    expect(titleWidget.style?.fontWeight, FontWeight.w400);
    expect(titleWidget.maxLines, 3);
  });

  testWidgets('DreamCard shows analyzing and failed states', (tester) async {
    await tester.pumpWidget(
      wrapWithMaterial(
        Row(
          children: [
            SizedBox(
              width: 180,
              height: 180,
              child: DreamCard(
                dream: buildDream(id: 'dream-a', analysisStatus: 'analyzing'),
                accentColor: Colors.orange,
              ),
            ),
            SizedBox(
              width: 180,
              height: 180,
              child: DreamCard(
                dream: buildDream(
                  id: 'dream-b',
                  analysisStatus: 'analysis_failed',
                  title: null,
                  content: 'Fallback content title',
                ),
                accentColor: Colors.orange,
              ),
            ),
          ],
        ),
      ),
    );

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.byIcon(Icons.error_outline), findsOneWidget);
    expect(find.text('Fallback content title'), findsOneWidget);
  });
}
