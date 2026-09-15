import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/api_config.dart';
import '../models/student.dart';
import 'api_service.dart';

class AuthResult {
  final bool success;
  final String? error;
  final String? accessToken;
  final String? role;

  AuthResult({required this.success, this.error, this.accessToken, this.role});
}

class AuthService {
  final ApiService _api;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  AuthService(this._api);

  Future<AuthResult> login(String email, String password) async {
    try {
      // Backend expects form-urlencoded data for OAuth2PasswordRequestForm
      final response = await _api.postForm(
        '/auth/login',
        data: {
          'username': email,
          'password': password,
        },
      );

      if (response.statusCode == 200) {
        final data = response.data;
        final accessToken = data['access_token'];
        final refreshToken = data['refresh_token'];
        final role = data['role'] as String? ?? 'student';

        await _storage.write(key: ApiConfig.tokenKey, value: accessToken);
        await _storage.write(key: 'user_role', value: role);
        if (refreshToken != null) {
          await _storage.write(key: ApiConfig.refreshTokenKey, value: refreshToken);
        }

        return AuthResult(success: true, accessToken: accessToken, role: role);
      }

      return AuthResult(success: false, error: 'Login failed');
    } on DioException catch (e) {
      if (e.response?.statusCode == 400 || e.response?.statusCode == 401) {
        return AuthResult(success: false, error: 'Invalid email or password');
      }
      return AuthResult(success: false, error: 'Connection error. Please try again.');
    } catch (e) {
      return AuthResult(success: false, error: 'An unexpected error occurred');
    }
  }

  Future<void> logout() async {
    try {
      await _api.post('/auth/logout');
    } catch (_) {
      // Ignore errors during logout
    } finally {
      await _storage.delete(key: ApiConfig.tokenKey);
      await _storage.delete(key: ApiConfig.refreshTokenKey);
      await _storage.delete(key: 'user_role');
    }
  }

  Future<bool> isLoggedIn() async {
    final token = await _storage.read(key: ApiConfig.tokenKey);
    return token != null;
  }

  Future<String> getRole() async {
    final role = await _storage.read(key: 'user_role');
    return role ?? 'student';
  }

  Future<DashboardData?> getDashboard() async {
    try {
      final response = await _api.get('/students/me/dashboard');
      if (response.statusCode == 200) {
        return DashboardData.fromJson(response.data);
      }
      return null;
    } catch (e) {
      return null;
    }
  }
}
