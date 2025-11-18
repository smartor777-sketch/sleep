import 'package:flutter/foundation.dart';

class Dream {
  final String id;
  final String content;
  final DateTime createdAt;

  Dream({
    required this.id,
    required this.content,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  // Для упрощённого копирования с изменением полей
  Dream copyWith({
    String? id,
    String? content,
    DateTime? createdAt,
  }) {
    return Dream(
      id: id ?? this.id,
      content: content ?? this.content,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  String toString() => content;
}