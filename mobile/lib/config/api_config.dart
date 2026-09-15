class ApiConfig {
  static const String baseUrl = 'http://10.0.2.2:8000/api/v1';

  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);

  static const String tokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
}
