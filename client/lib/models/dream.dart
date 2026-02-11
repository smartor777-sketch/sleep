class Dream {
  final String id;
  final String userId;
  final String? title;
  final String content;
  final String emoji;
  final String comment;
  final DateTime recordedAt;
  final DateTime createdAt;
  final DateTime updatedAt;
  final bool hasAnalysis;

  Dream({
    required this.id,
    required this.userId,
    required this.title,
    required this.content,
    required this.emoji,
    required this.comment,
    required this.recordedAt,
    required this.createdAt,
    required this.updatedAt,
    required this.hasAnalysis,
  });

  factory Dream.fromJson(Map<String, dynamic> json) {
    return Dream(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      title: json['title'] as String?,
      content: json['content'] as String,
      emoji: json['emoji'] as String? ?? '',
      comment: json['comment'] as String? ?? '',
      recordedAt: DateTime.parse(json['recorded_at'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      hasAnalysis: json['has_analysis'] as bool? ?? false,
    );
  }

  // Для упрощённого копирования с изменением полей
  Dream copyWith({
    String? id,
    String? userId,
    String? title,
    String? content,
    String? emoji,
    String? comment,
    DateTime? recordedAt,
    DateTime? createdAt,
    DateTime? updatedAt,
    bool? hasAnalysis,
  }) {
    return Dream(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      title: title ?? this.title,
      content: content ?? this.content,
      emoji: emoji ?? this.emoji,
      comment: comment ?? this.comment,
      recordedAt: recordedAt ?? this.recordedAt,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      hasAnalysis: hasAnalysis ?? this.hasAnalysis,
    );
  }

  @override
  String toString() => content;
}
