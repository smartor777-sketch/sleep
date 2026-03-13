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
  final String analysisStatus;
  final String? analysisErrorMessage;
  final String? gradientColor1;
  final String? gradientColor2;

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
    required this.analysisStatus,
    required this.analysisErrorMessage,
    required this.gradientColor1,
    required this.gradientColor2,
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
      analysisStatus: json['analysis_status'] as String? ?? 'saved',
      analysisErrorMessage: json['analysis_error_message'] as String?,
      gradientColor1: json['gradient_color_1'] as String?,
      gradientColor2: json['gradient_color_2'] as String?,
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
    String? analysisStatus,
    String? analysisErrorMessage,
    String? gradientColor1,
    String? gradientColor2,
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
      analysisStatus: analysisStatus ?? this.analysisStatus,
      analysisErrorMessage: analysisErrorMessage ?? this.analysisErrorMessage,
      gradientColor1: gradientColor1 ?? this.gradientColor1,
      gradientColor2: gradientColor2 ?? this.gradientColor2,
    );
  }

  @override
  String toString() => content;
}
