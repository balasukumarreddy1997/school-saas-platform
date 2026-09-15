import 'package:flutter/foundation.dart';
import '../models/student.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

class AppState extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  late final AuthService _authService;

  AuthStatus _authStatus = AuthStatus.unknown;
  DashboardData? _dashboardData;
  bool _isLoading = false;
  String? _error;

  AppState() {
    _authService = AuthService(_apiService);
    _checkAuthStatus();
  }

  AuthStatus get authStatus => _authStatus;
  DashboardData? get dashboardData => _dashboardData;
  bool get isLoading => _isLoading;
  String? get error => _error;
  Student? get student => _dashboardData?.student;

  Future<void> _checkAuthStatus() async {
    final isLoggedIn = await _authService.isLoggedIn();
    if (isLoggedIn) {
      _authStatus = AuthStatus.authenticated;
      await loadDashboard();
    } else {
      _authStatus = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    final result = await _authService.login(email, password);

    if (result.success) {
      _authStatus = AuthStatus.authenticated;
      await loadDashboard();
      _isLoading = false;
      notifyListeners();
      return true;
    } else {
      _error = result.error;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();

    await _authService.logout();

    _authStatus = AuthStatus.unauthenticated;
    _dashboardData = null;
    _isLoading = false;
    notifyListeners();
  }

  Future<void> loadDashboard() async {
    _isLoading = true;
    notifyListeners();

    _dashboardData = await _authService.getDashboard();

    _isLoading = false;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
