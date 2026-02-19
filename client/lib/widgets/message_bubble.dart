import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:markdown/markdown.dart' as md;

class MessageBubble extends StatelessWidget {
  final String message;
  final bool isUserMessage;
  final VoidCallback? onLongPress;
  final GestureLongPressStartCallback? onLongPressStart;
  final Color accentColor;

  const MessageBubble({
    super.key,
    this.isUserMessage = true,
    this.onLongPress,
    this.onLongPressStart,
    required this.message,
    required this.accentColor,
  });

  @override
  Widget build(BuildContext context) {
    final onAccentColor =
        accentColor.computeLuminance() > 0.5 ? Colors.black : Colors.white;
    final neutralColor = Theme.of(context).colorScheme.surfaceVariant;
    final neutralOnColor = Theme.of(context).colorScheme.onSurfaceVariant;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: Align(
        alignment:
            isUserMessage ? Alignment.centerRight : Alignment.centerLeft,
        child: GestureDetector(
          onLongPress: onLongPress,
          onLongPressStart: onLongPressStart,
          child: Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: isUserMessage ? accentColor : neutralColor,
              borderRadius: BorderRadius.circular(12),
            ),
            child: isUserMessage
                ? Text(
                    message,
                    style: TextStyle(color: onAccentColor),
                  )
                : MarkdownBody(
                    data: message,
                    shrinkWrap: true,
                    softLineBreak: true,
                    extensionSet: md.ExtensionSet.gitHubFlavored,
                    styleSheet: MarkdownStyleSheet(
                      p: TextStyle(color: neutralOnColor),
                      strong: TextStyle(color: neutralOnColor, fontWeight: FontWeight.bold),
                      em: TextStyle(color: neutralOnColor, fontStyle: FontStyle.italic),
                      code: TextStyle(
                        color: neutralOnColor,
                        backgroundColor: neutralColor.withOpacity(0.5),
                        fontFamily: 'monospace',
                      ),
                      h1: TextStyle(color: neutralOnColor, fontWeight: FontWeight.bold),
                      h2: TextStyle(color: neutralOnColor, fontWeight: FontWeight.bold),
                      h3: TextStyle(color: neutralOnColor, fontWeight: FontWeight.bold),
                      blockquotePadding: const EdgeInsets.only(left: 8),
                      blockquoteDecoration: BoxDecoration(
                        border: Border(
                          left: BorderSide(color: neutralOnColor.withOpacity(0.4), width: 3),
                        ),
                      ),
                    ),
                  ),
          ),
        ),
      ),
    );
  }
}