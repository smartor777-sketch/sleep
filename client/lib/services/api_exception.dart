class ApiException implements Exception {
  final int statusCode;
  final String message;

  ApiException(this.statusCode, this.message);

  bool get isPaymentRequired => statusCode == 402;

  @override
  String toString() => 'ApiException($statusCode): $message';
}

class AnalysisLimitException implements Exception {
  @override
  String toString() => 'analysis_limit_reached';
}
