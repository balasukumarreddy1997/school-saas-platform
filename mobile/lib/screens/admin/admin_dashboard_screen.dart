import 'package:flutter/material.dart';
import '../../config/theme.dart';
import '../../services/api_service.dart';
import 'manage_students_screen.dart';
import 'manage_teachers_screen.dart';
import 'manage_subjects_screen.dart';

class AdminDashboardScreen extends StatefulWidget {
  final VoidCallback onLogout;

  const AdminDashboardScreen({super.key, required this.onLogout});

  @override
  State<AdminDashboardScreen> createState() => _AdminDashboardScreenState();
}

class _AdminDashboardScreenState extends State<AdminDashboardScreen> {
  final ApiService _api = ApiService();
  Map<String, dynamic>? _stats;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadDashboard();
  }

  Future<void> _loadDashboard() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });
      final response = await _api.get('/admin/dashboard');
      setState(() {
        _stats = response.data as Map<String, dynamic>;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load dashboard';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(_error!),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: _loadDashboard,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  )
                : RefreshIndicator(
                    onRefresh: _loadDashboard,
                    child: ListView(
                      padding: const EdgeInsets.all(20),
                      children: [
                        _buildHeader(),
                        const SizedBox(height: 24),
                        _buildStatsGrid(),
                        const SizedBox(height: 24),
                        _buildManagementSection(),
                        const SizedBox(height: 24),
                        _buildQuickActions(),
                      ],
                    ),
                  ),
      ),
    );
  }

  Widget _buildHeader() {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Admin Dashboard',
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              Text(
                'St Joseph\'s Public School',
                style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
              ),
            ],
          ),
        ),
        GestureDetector(
          onTap: () => _showProfileMenu(context),
          child: CircleAvatar(
            radius: 24,
            backgroundColor: Colors.purple.shade600,
            child: const Text(
              'A',
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildStatsGrid() {
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.4,
      children: [
        _buildStatCard(
          'Students',
          '${_stats?['total_students'] ?? 0}',
          Icons.people,
          Colors.blue,
        ),
        _buildStatCard(
          'Teachers',
          '${_stats?['total_teachers'] ?? 0}',
          Icons.school,
          Colors.green,
        ),
        _buildStatCard(
          'Subjects',
          '${_stats?['total_subjects'] ?? 0}',
          Icons.menu_book,
          Colors.orange,
        ),
        _buildStatCard(
          'Attendance Today',
          '${_stats?['attendance_today'] ?? 0}',
          Icons.fact_check,
          Colors.purple,
        ),
      ],
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            title,
            style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
          ),
        ],
      ),
    );
  }

  Widget _buildManagementSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Management',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        _buildManagementTile(
          'Manage Students',
          'Add, edit, or remove students',
          Icons.people_outline,
          Colors.blue,
          () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const ManageStudentsScreen()),
          ),
        ),
        const SizedBox(height: 8),
        _buildManagementTile(
          'Manage Teachers',
          'Add, edit, or remove teachers',
          Icons.school_outlined,
          Colors.green,
          () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const ManageTeachersScreen()),
          ),
        ),
        const SizedBox(height: 8),
        _buildManagementTile(
          'Manage Subjects',
          'Add, edit, or remove subjects',
          Icons.menu_book_outlined,
          Colors.orange,
          () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const ManageSubjectsScreen()),
          ),
        ),
      ],
    );
  }

  Widget _buildManagementTile(
    String title,
    String subtitle,
    IconData icon,
    Color color,
    VoidCallback onTap,
  ) {
    return Card(
      child: ListTile(
        leading: Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: color),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }

  Widget _buildQuickActions() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Quick Actions',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildActionButton(
                'Reports',
                Icons.assessment,
                Colors.indigo,
                () => ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Coming soon!')),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildActionButton(
                'Settings',
                Icons.settings,
                Colors.grey,
                () => ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Coming soon!')),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildActionButton(
    String title,
    IconData icon,
    Color color,
    VoidCallback onTap,
  ) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(height: 8),
            Text(title, style: TextStyle(color: color, fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }

  void _showProfileMenu(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const SizedBox(height: 8),
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 16),
              ListTile(
                leading: const Icon(Icons.logout, color: Colors.red),
                title: const Text('Logout', style: TextStyle(color: Colors.red)),
                onTap: () {
                  Navigator.pop(context);
                  widget.onLogout();
                },
              ),
              const SizedBox(height: 16),
            ],
          ),
        );
      },
    );
  }
}
