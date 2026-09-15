class Student {
  final String id;
  final String userId;
  final String email;
  final String firstName;
  final String lastName;
  final String admissionNumber;
  final String? rollNumber;
  final String? dateOfBirth;
  final String? gender;
  final String? parentName;
  final String? parentPhone;

  Student({
    required this.id,
    required this.userId,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.admissionNumber,
    this.rollNumber,
    this.dateOfBirth,
    this.gender,
    this.parentName,
    this.parentPhone,
  });

  String get fullName => '$firstName $lastName';

  factory Student.fromJson(Map<String, dynamic> json) {
    return Student(
      id: json['id'],
      userId: json['user_id'],
      email: json['email'],
      firstName: json['first_name'],
      lastName: json['last_name'],
      admissionNumber: json['admission_number'],
      rollNumber: json['roll_number'],
      dateOfBirth: json['date_of_birth'],
      gender: json['gender'],
      parentName: json['parent_name'],
      parentPhone: json['parent_phone'],
    );
  }
}

class DashboardData {
  final Student student;
  final AttendanceSummary attendance;
  final List<dynamic> recentResults;
  final List<dynamic> announcements;

  DashboardData({
    required this.student,
    required this.attendance,
    required this.recentResults,
    required this.announcements,
  });

  factory DashboardData.fromJson(Map<String, dynamic> json) {
    return DashboardData(
      student: Student.fromJson(json['student']),
      attendance: AttendanceSummary.fromJson(json['attendance']),
      recentResults: json['recent_results'] ?? [],
      announcements: json['announcements'] ?? [],
    );
  }
}

class AttendanceSummary {
  final int totalDays;
  final int present;
  final int absent;
  final double percentage;

  AttendanceSummary({
    required this.totalDays,
    required this.present,
    required this.absent,
    required this.percentage,
  });

  factory AttendanceSummary.fromJson(Map<String, dynamic> json) {
    return AttendanceSummary(
      totalDays: json['total_days'] ?? 0,
      present: json['present'] ?? 0,
      absent: json['absent'] ?? 0,
      percentage: (json['percentage'] ?? 0).toDouble(),
    );
  }
}
