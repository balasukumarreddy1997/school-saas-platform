import 'package:flutter/foundation.dart';
import '../models/student.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }
enum UserRole { student, teacher, admin }

class AppState extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  late final AuthService _authService;

  AuthStatus _authStatus = AuthStatus.unknown;
  UserRole _userRole = UserRole.student;
  DashboardData? _dashboardData;
  bool _isLoading = false;
  String? _error;

  AppState() {
    _authService = AuthService(_apiService);
    _checkAuthStatus();
  }

  AuthStatus get authStatus => _authStatus;
  UserRole get userRole => _userRole;
  DashboardData? get dashboardData => _dashboardData;
  bool get isLoading => _isLoading;
  String? get error => _error;
  Student? get student => _dashboardData?.student;

  Future<void> _checkAuthStatus() async {
    final isLoggedIn = await _authService.isLoggedIn();
    if (isLoggedIn) {
      _authStatus = AuthStatus.authenticated;
      final role = await _authService.getRole();
      _userRole = _parseRole(role);
      if (_userRole == UserRole.student) {
        await loadDashboard();
      }
    } else {
      _authStatus = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  UserRole _parseRole(String role) {
    switch (role.toLowerCase()) {
      case 'teacher':
        return UserRole.teacher;
      case 'admin':
        return UserRole.admin;
      default:
        return UserRole.student;
    }
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    final result = await _authService.login(email, password);

    if (result.success) {
      _authStatus = AuthStatus.authenticated;
      _userRole = _parseRole(result.role ?? 'student');
      if (_userRole == UserRole.student) {
        await loadDashboard();
      }
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
