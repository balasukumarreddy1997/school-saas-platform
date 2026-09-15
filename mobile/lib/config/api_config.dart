import 'package:flutter/foundation.dart' show kIsWeb;

class ApiConfig {
  // Your PC's WiFi IP - change this if your network changes
  static const String _pcIp = '192.168.1.6';

  static String get baseUrl {
    if (kIsWeb) {
      return 'http://localhost:8000/api/v1';
    }
    // Use PC's WiFi IP for physical devices
    return 'http://$_pcIp:8000/api/v1';
  }

  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);

  static const String tokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
}
