import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'config/theme.dart';
import 'providers/app_state.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/teacher/teacher_dashboard_screen.dart';

void main() {
  runApp(const SchoolApp());
}

class SchoolApp extends StatelessWidget {
  const SchoolApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AppState(),
      child: MaterialApp(
        title: 'School App',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        home: const AuthWrapper(),
      ),
    );
  }
}

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    final authStatus = appState.authStatus;
    final userRole = appState.userRole;

    switch (authStatus) {
      case AuthStatus.unknown:
        return const Scaffold(
          body: Center(
            child: CircularProgressIndicator(),
          ),
        );
      case AuthStatus.authenticated:
        switch (userRole) {
          case UserRole.teacher:
            return TeacherDashboardScreen(
              onLogout: () => appState.logout(),
            );
          case UserRole.admin:
            // TODO: Add admin dashboard
            return TeacherDashboardScreen(
              onLogout: () => appState.logout(),
            );
          case UserRole.student:
            return const DashboardScreen();
        }
      case AuthStatus.unauthenticated:
        return const LoginScreen();
    }
  }
}
