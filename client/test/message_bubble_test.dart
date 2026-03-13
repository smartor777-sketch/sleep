import 'package:client/widgets/message_bubble.dart';
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_test/flutter_test.dart';

import 'test_helpers.dart';

void main() {
  testWidgets('assistant messages render markdown body', (tester) async {
    await tester.pumpWidget(
      wrapWithMaterial(
        const MessageBubble(
          message: '## Heading\n\n- one\n- two\n\n**bold** text',
          isUserMessage: false,
          accentColor: Colors.orange,
        ),
      ),
    );

    expect(find.byType(MarkdownBody), findsOneWidget);
    expect(find.text('Heading'), findsOneWidget);
    expect(find.text('one'), findsOneWidget);
    expect(find.text('two'), findsOneWidget);
    expect(find.textContaining('text'), findsOneWidget);
  });

  testWidgets('user messages stay plain text', (tester) async {
    await tester.pumpWidget(
      wrapWithMaterial(
        const MessageBubble(
          message: '**not markdown for user**',
          isUserMessage: true,
          accentColor: Colors.orange,
        ),
      ),
    );

    expect(find.byType(MarkdownBody), findsNothing);
    expect(find.text('**not markdown for user**'), findsOneWidget);
  });
}
