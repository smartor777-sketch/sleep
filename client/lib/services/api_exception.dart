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

/// Backend responded with 409 — analysis is already running for this dream.
/// Not an error from the user's perspective: just start polling for status.
class AnalysisAlreadyRunningException implements Exception {
  @override
  String toString() => 'analysis_already_running';
}
