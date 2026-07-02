import 'package:flutter/material.dart';

import '../services/billing_service.dart';

class BillingProvider extends ChangeNotifier {
  BillingProvider(this._service);

  final BillingService _service;

  BillingStatus? _status;
  bool _loading = false;
  bool _creatingPayment = false;
  String? _error;

  BillingStatus? get status => _status;
  bool get loading => _loading;
  bool get creatingPayment => _creatingPayment;
  String? get error => _error;

  bool get hasFullAccess => _status?.hasFullAccess ?? false;
  bool get isFree => _status?.isFree ?? true;
  int? get analysesLeft => _status?.analysesLeftThisWeek;

  Future<void> initialize() async {
    try {
      await _service.initialize();
    } catch (_) {}
    await refresh();
  }

  Future<void> refresh() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      _status = await _service.getStatus();
    } catch (e) {
      _error = e.toString();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<String> createPayment(String planId) async {
    _creatingPayment = true;
    _error = null;
    notifyListeners();

    try {
      final result = await _service.createPayment(planId: planId);
      return result.confirmationUrl;
    } catch (e) {
      _error = e.toString();
      rethrow;
    } finally {
      _creatingPayment = false;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _service.dispose();
    super.dispose();
  }
}
