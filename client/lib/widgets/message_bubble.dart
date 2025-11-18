import 'package:flutter/material.dart';

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
            child: Text(
              message,
              style: TextStyle(
                color: isUserMessage ? onAccentColor : neutralOnColor,
              ),
            ),
          ),
        ),
      ),
    );
  }
}