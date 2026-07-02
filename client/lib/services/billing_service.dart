import 'dart:convert';

import 'api_client.dart';

class BillingStatus {
  final String subType;
  final String? subExpiresAt;
  final int trialDaysLeft;
  final int? analysesLeftThisWeek;

  BillingStatus({
    required this.subType,
    this.subExpiresAt,
    this.trialDaysLeft = 0,
    this.analysesLeftThisWeek,
  });

  bool get isPro => subType == 'pro';
  bool get isTrial => subType == 'trial';
  bool get isFree => subType == 'free';
  bool get hasFullAccess => isPro || isTrial;

  factory BillingStatus.fromJson(Map<String, dynamic> json) {
    return BillingStatus(
      subType: json['sub_type'] as String? ?? 'free',
      subExpiresAt: json['sub_expires_at'] as String?,
      trialDaysLeft: json['trial_days_left'] as int? ?? 0,
      analysesLeftThisWeek: json['analyses_left_this_week'] as int?,
    );
  }
}

class PaymentCreateResult {
  final String paymentId;
  final String status;
  final String planId;
  final String confirmationUrl;
  final String? expiresAt;

  PaymentCreateResult({
    required this.paymentId,
    required this.status,
    required this.planId,
    required this.confirmationUrl,
    this.expiresAt,
  });

  factory PaymentCreateResult.fromJson(Map<String, dynamic> json) {
    return PaymentCreateResult(
      paymentId: json['payment_id'] as String,
      status: json['status'] as String? ?? 'pending',
      planId: json['plan_id'] as String,
      confirmationUrl: json['confirmation_url'] as String,
      expiresAt: json['expires_at'] as String?,
    );
  }
}

class BillingService {
  BillingService(this._api);

  final ApiClient _api;

  Future<void> initialize() async {}

  void dispose() {}

  Future<PaymentCreateResult> createPayment({
    required String planId,
    String? returnUrl,
  }) async {
    final body = <String, Object?>{'plan_id': planId};
    if (returnUrl != null) body['return_url'] = returnUrl;
    final response = await _api.post(
      '/api/v1/billing/create-payment',
      body: body,
    );
    if (response.statusCode != 200) {
      throw Exception('payment_creation_failed');
    }
    return PaymentCreateResult.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<BillingStatus> getStatus() async {
    final response = await _api.get('/api/v1/billing/status');
    if (response.statusCode != 200) {
      throw Exception('billing_status_failed');
    }
    return BillingStatus.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }
}
