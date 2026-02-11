import 'dart:convert';

import 'package:http/http.dart' as http;

import 'api_client.dart';
import 'api_exception.dart';

class Stats {
  final int totalDreams;
  final int streakDays;
  final Map<String, int> dreamsByWeekday;
  final String? avgTimeOfDay;

  Stats({
    required this.totalDreams,
    required this.streakDays,
    required this.dreamsByWeekday,
    required this.avgTimeOfDay,
  });

  factory Stats.fromJson(Map<String, dynamic> json) {
    return Stats(
      totalDreams: json['total_dreams'] as int? ?? 0,
      streakDays: json['streak_days'] as int? ?? 0,
      dreamsByWeekday: (json['dreams_by_weekday'] as Map<String, dynamic>? ?? {})
          .map((k, v) => MapEntry(k, v as int)),
      avgTimeOfDay: json['avg_time_of_day'] as String?,
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
