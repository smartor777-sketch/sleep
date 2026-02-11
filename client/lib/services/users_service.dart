import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/user_me.dart';
import 'api_client.dart';
import 'api_exception.dart';

class UsersService {
  UsersService(this._api);

  final ApiClient _api;

  Future<UserMe> updateMe({String? aboutMe, String? timezone}) async {
    final response = await _api.put(
      '/api/v1/users/me',
      body: {
        if (aboutMe != null) 'self_description': aboutMe,
        if (timezone != null) 'timezone': timezone,
      },
    );

    if (response.statusCode != 200) {
      _throwApi(response);
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return UserMe.fromJson(data);
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
