enum MessageRole { user, assistant, system }

class AnalysisMessage {
  final String id;
  final String? dreamId;
  final String content;
  final MessageRole role;
  final DateTime createdAt;

  AnalysisMessage({
    required this.id,
    this.dreamId,
    required this.content,
    required this.role,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  factory AnalysisMessage.fromJson(Map<String, dynamic> json) {
    return AnalysisMessage(
      id: json['id'] as String,
      dreamId: json['dream_id'] as String?,
      content: json['content'] as String,
      role: MessageRole.values.firstWhere(
        (r) => r.name == json['role'],
        orElse: () => MessageRole.assistant,
      ),
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'dream_id': dreamId,
      'content': content,
      'role': role.name,
      'created_at': createdAt.toIso8601String(),
    };
  }
}
