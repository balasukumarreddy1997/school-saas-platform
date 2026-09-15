class User {
  final String id;
  final String email;
  final String firstName;
  final String lastName;
  final String schoolId;
  final bool isActive;
  final DateTime? lastLoginAt;

  User({
    required this.id,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.schoolId,
    required this.isActive,
    this.lastLoginAt,
  });

  String get fullName => '$firstName $lastName';

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      firstName: json['first_name'],
      lastName: json['last_name'],
      schoolId: json['school_id'],
      isActive: json['is_active'] ?? true,
      lastLoginAt: json['last_login_at'] != null
          ? DateTime.parse(json['last_login_at'])
          : null,
    );
  }
}
