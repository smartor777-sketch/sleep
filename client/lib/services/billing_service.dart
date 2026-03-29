import 'dart:async';
import 'dart:convert';

import 'package:in_app_purchase/in_app_purchase.dart';

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

class BillingService {
  BillingService(this._api);

  final ApiClient _api;
  final InAppPurchase _iap = InAppPurchase.instance;

  static const _productIds = <String>{
    'pro_weekly',
    'pro_monthly',
    'pro_yearly',
  };

  StreamSubscription<List<PurchaseDetails>>? _purchaseSub;

  /// Callback set by BillingProvider to handle purchase updates.
  void Function(List<PurchaseDetails>)? onPurchaseUpdate;

  Future<bool> isAvailable() => _iap.isAvailable();

  Future<void> initialize() async {
    _purchaseSub = _iap.purchaseStream.listen(_handlePurchaseUpdate);
  }

  void dispose() {
    _purchaseSub?.cancel();
  }

  Future<List<ProductDetails>> loadProducts() async {
    final response = await _iap.queryProductDetails(_productIds);
    return response.productDetails;
  }

  Future<void> buy(ProductDetails product) async {
    final param = PurchaseParam(productDetails: product);
    await _iap.buyNonConsumable(purchaseParam: param);
  }

  Future<void> restorePurchases() async {
    await _iap.restorePurchases();
  }

  /// Verify purchase on our backend.
  Future<Map<String, dynamic>> verifyPurchase({
    required String purchaseToken,
    required String productId,
  }) async {
    final response = await _api.post(
      '/api/v1/billing/verify-purchase',
      body: {
        'purchase_token': purchaseToken,
        'product_id': productId,
      },
    );
    if (response.statusCode != 200) {
      throw Exception('purchase_verification_failed');
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  /// Get billing status from backend.
  Future<BillingStatus> getStatus() async {
    final response = await _api.get('/api/v1/billing/status');
    if (response.statusCode != 200) {
      throw Exception('billing_status_failed');
    }
    return BillingStatus.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  void _handlePurchaseUpdate(List<PurchaseDetails> purchases) {
    onPurchaseUpdate?.call(purchases);
  }
}
