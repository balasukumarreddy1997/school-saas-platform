class ApiConfig {
  // Cloud API URL (Railway deployment)
  static const String baseUrl = 'https://school-saas-platform-production-475f.up.railway.app/api/v1';

  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);

  static const String tokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
}
