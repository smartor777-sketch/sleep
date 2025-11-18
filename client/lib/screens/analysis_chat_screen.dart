import 'package:flutter/material.dart';
import '../widgets/message_bubble.dart';
import '../models/dream.dart';
import '../models/analysis_message.dart';

class AnalysisChatScreen extends StatefulWidget {
  final Dream dream;
  final Color accentColor;
  final Function(Color) setAccentColor;

  const AnalysisChatScreen({
    super.key,
    required this.dream,
    required this.accentColor,
    required this.setAccentColor,
  });

  @override
  State<AnalysisChatScreen> createState() => _AnalysisChatScreenState();
}

class _AnalysisChatScreenState extends State<AnalysisChatScreen> {
  final List<AnalysisMessage> _messages = [];
  final TextEditingController _controller = TextEditingController();
  bool _isLoading = false;
  Dream? _editingDream;
  late Color _accentColor;

  @override
  void initState() {
    super.initState();
    _accentColor = widget.accentColor;
    _initChat();
  }

  @override
  void didUpdateWidget(covariant AnalysisChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.accentColor != widget.accentColor) {
      setState(() {
        _accentColor = widget.accentColor;
      });
    }
  }

  void _handleAccentColorChange(Color color) {
    if (_accentColor == color) return;
    setState(() {
      _accentColor = color;
    });
    widget.setAccentColor(color);
  }

  void _initChat() {
    // Первое сообщение — текст сна пользователя
    _messages.add(
      AnalysisMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        content: widget.dream.content,
        sender: Sender.user,
      ),
    );

    // Сразу добавляем заглушку ответа LLM
    _simulateLLMResponse(widget.dream.content);
  }

  void _simulateLLMResponse(String dreamText) async {
    setState(() => _isLoading = true);

    await Future.delayed(const Duration(seconds: 1)); // имитация запроса

    setState(() {
      _messages.add(
        AnalysisMessage(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          content: "Это пример анализа сна: '$dreamText'",
          sender: Sender.llm,
        ),
      );
      _isLoading = false;
    });
  }

  void _sendMessage() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add(
        AnalysisMessage(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          content: text,
          sender: Sender.user,
        ),
      );
      _controller.clear();
    });

    // Можно имитировать ответ LLM
    _simulateLLMResponse(text);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Анализ сна'),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              reverse: true,
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[_messages.length - 1 - index];
                return MessageBubble(
                  message: message.content,
                  isUserMessage: message.sender == Sender.user,
                  accentColor: _accentColor,
                );
              },
            ),
          ),
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.all(8.0),
              child: CircularProgressIndicator(),
            ),
          Container(
            margin: const EdgeInsets.all(12),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: Theme.of(context).brightness == Brightness.dark
                  ? Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.4)
                  : Theme.of(context).colorScheme.surfaceVariant,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
              ),
            ),
            child: Row(
              children: [
                IconButton(
                  icon: Icon(Icons.mic, color: _accentColor),
                  onPressed: () {
                    // TODO: голосовой ввод
                  },
                ),

                Expanded(
                  child: TextField(
                    controller: _controller,
                    maxLines: null,
                    decoration: InputDecoration(
                      hintText: _editingDream != null
                          ? 'Редактировать сон...'
                          : 'Напишите сон...',
                      border: InputBorder.none,
                    ),
                  ),
                ),

                const SizedBox(width: 8),

                Container(
                  decoration: BoxDecoration(
                    color: _accentColor,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: IconButton(
                    icon: const Icon(Icons.send, color: Colors.white),
                    onPressed: _sendMessage,
                  ),
                )
              ],
            ),
          )
        ],
      ),
    );
  }
}