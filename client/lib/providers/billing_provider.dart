import 'dart:async';

import 'package:flutter/material.dart';
import 'package:in_app_purchase/in_app_purchase.dart';

import '../services/billing_service.dart';

class BillingProvider extends ChangeNotifier {
  BillingProvider(this._service);

  final BillingService _service;

  List<ProductDetails> _products = [];
  BillingStatus? _status;
  bool _loading = false;
  String? _error;
  bool _purchasing = false;

  List<ProductDetails> get products => _products;
  BillingStatus? get status => _status;
  bool get loading => _loading;
  String? get error => _error;
  bool get purchasing => _purchasing;

  bool get hasFullAccess => _status?.hasFullAccess ?? false;
  bool get isFree => _status?.isFree ?? true;
  int? get analysesLeft => _status?.analysesLeftThisWeek;

  Future<void> initialize() async {
    _service.onPurchaseUpdate = _onPurchaseUpdate;
    try {
      await _service.initialize();
    } catch (_) {
      // IAP not available (no Google Play Services, etc.)
    }
    await refresh();
  }

  Future<void> refresh() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final available = await _service.isAvailable();
      if (available) {
        _products = await _service.loadProducts();
        // Sort: weekly, monthly, yearly
        _products.sort((a, b) => a.rawPrice.compareTo(b.rawPrice));
      }
      _status = await _service.getStatus();
    } catch (e) {
      _error = e.toString();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> buy(ProductDetails product) async {
    _purchasing = true;
    _error = null;
    notifyListeners();

    try {
      await _service.buy(product);
    } catch (e) {
      _purchasing = false;
      _error = e.toString();
      notifyListeners();
    }
  }

  Future<void> restorePurchases() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _service.restorePurchases();
    } catch (e) {
      _error = e.toString();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> _onPurchaseUpdate(List<PurchaseDetails> purchases) async {
    for (final p in purchases) {
      if (p.status == PurchaseStatus.purchased ||
          p.status == PurchaseStatus.restored) {
        // Verify on backend
        try {
          final token = p.verificationData.serverVerificationData;
          await _service.verifyPurchase(
            purchaseToken: token,
            productId: p.productID,
          );
        } catch (_) {
          // Verification failed — still complete the purchase to avoid re-delivery
        }

        // Mark purchase as completed
        if (p.pendingCompletePurchase) {
          await InAppPurchase.instance.completePurchase(p);
        }
      }

      if (p.status == PurchaseStatus.error) {
        _error = p.error?.message ?? 'purchase_failed';
      }
    }

    _purchasing = false;

    // Refresh status from backend
    try {
      _status = await _service.getStatus();
    } catch (_) {}

    notifyListeners();
  }

  @override
  void dispose() {
    _service.dispose();
    super.dispose();
  }
}
