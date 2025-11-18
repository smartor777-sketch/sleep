enum Sender { user, llm }

class AnalysisMessage {
  final String id;
  final String content;
  final Sender sender;
  final DateTime createdAt;

  AnalysisMessage({
    required this.id,
    required this.content,
    required this.sender,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();
}