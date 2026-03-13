import 'dart:convert';

import 'package:http/http.dart' as http;

import 'api_client.dart';
import 'api_exception.dart';

class Stats {
  final int totalDreams;
  final int streakDays;
  final Map<String, int> dreamsByWeekday;
  final List<DayCount> dreamsLast14Days;
  final List<ArchetypeCount> archetypesTop;
  final String? avgTimeOfDay;

  Stats({
    required this.totalDreams,
    required this.streakDays,
    required this.dreamsByWeekday,
    required this.dreamsLast14Days,
    required this.archetypesTop,
    required this.avgTimeOfDay,
  });

  factory Stats.fromJson(Map<String, dynamic> json) {
    return Stats(
      totalDreams: json['total_dreams'] as int? ?? 0,
      streakDays: json['streak_days'] as int? ?? 0,
      dreamsByWeekday: (json['dreams_by_weekday'] as Map<String, dynamic>? ?? {})
          .map((k, v) => MapEntry(k, v as int)),
      dreamsLast14Days: (json['dreams_last_14_days'] as List<dynamic>? ?? [])
          .map((e) => DayCount.fromJson(e as Map<String, dynamic>))
          .toList(),
      archetypesTop: (json['archetypes_top'] as List<dynamic>? ?? [])
          .map((e) => ArchetypeCount.fromJson(e as Map<String, dynamic>))
          .toList(),
      avgTimeOfDay: json['avg_time_of_day'] as String?,
    );
  }
}

class DayCount {
  final String date;
  final int count;

  DayCount({required this.date, required this.count});

  factory DayCount.fromJson(Map<String, dynamic> json) {
    return DayCount(
      date: json['date'] as String? ?? '',
      count: json['count'] as int? ?? 0,
    );
  }
}

class ArchetypeCount {
  final String name;
  final int count;

  ArchetypeCount({required this.name, required this.count});

  factory ArchetypeCount.fromJson(Map<String, dynamic> json) {
    return ArchetypeCount(
      name: json['name'] as String? ?? '',
      count: json['count'] as int? ?? 0,
    );
  }
}

class StatsService {
  StatsService(this._api);

  final ApiClient _api;

  Future<Stats> getMyStats() async {
    final response = await _api.get('/api/v1/stats/me');
    if (response.statusCode != 200) {
      _throwApi(response);
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return Stats.fromJson(data);
  }

  void _throwApi(http.Response response) {
    String message = 'request_failed';
    try {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      message = data['detail']?.toString() ?? message;
    } catch (_) {}
    throw ApiException(response.statusCode, message);
  }
}
