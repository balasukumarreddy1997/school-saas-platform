import 'package:flutter/material.dart';
import '../../config/theme.dart';
import '../../services/api_service.dart';

class TeacherTimetableScreen extends StatefulWidget {
  const TeacherTimetableScreen({super.key});

  @override
  State<TeacherTimetableScreen> createState() => _TeacherTimetableScreenState();
}

class _TeacherTimetableScreenState extends State<TeacherTimetableScreen> with SingleTickerProviderStateMixin {
  final ApiService _api = ApiService();
  late TabController _tabController;
  Map<String, dynamic>? _data;
  bool _isLoading = true;
  String? _error;

  final List<String> _days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _days.length, vsync: this);
    _loadTimetable();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadTimetable() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });

      final response = await _api.get('/timetable/teacher-schedule');
      setState(() {
        _data = response.data as Map<String, dynamic>;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load timetable';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Schedule'),
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          indicatorColor: Colors.white,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: _days.map((d) => Tab(text: d.substring(0, 3))).toList(),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error_outline, size: 48, color: Colors.grey.shade400),
                      const SizedBox(height: 16),
                      Text(_error!, style: TextStyle(color: Colors.grey.shade600)),
                      const SizedBox(height: 16),
                      ElevatedButton(onPressed: _loadTimetable, child: const Text('Retry')),
                    ],
                  ),
                )
              : TabBarView(
                  controller: _tabController,
                  children: _days.map((day) => _buildDaySchedule(day)).toList(),
                ),
    );
  }

  Widget _buildDaySchedule(String day) {
    final byDay = _data?['by_day'] as Map<String, dynamic>? ?? {};
    final periods = byDay[day] as List<dynamic>? ?? [];

    if (periods.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.event_available, size: 64, color: Colors.grey.shade300),
            const SizedBox(height: 16),
            Text(
              'No classes on $day',
              style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadTimetable,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: periods.length,
        itemBuilder: (context, index) {
          final period = periods[index];
          return _buildPeriodCard(period, index);
        },
      ),
    );
  }

  Widget _buildPeriodCard(Map<String, dynamic> period, int index) {
    final colors = [
      Colors.teal,
      Colors.blue,
      Colors.orange,
      Colors.purple,
      Colors.green,
      Colors.pink,
      Colors.indigo,
    ];
    final color = colors[index % colors.length];

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            // Time block
            Container(
              width: 70,
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                children: [
                  Text(
                    period['start_time'] ?? '',
                    style: TextStyle(fontWeight: FontWeight.bold, color: color),
                  ),
                  const Text('-', style: TextStyle(color: Colors.grey)),
                  Text(
                    period['end_time'] ?? '',
                    style: TextStyle(fontWeight: FontWeight.bold, color: color),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 16),
            // Details
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    period['subject_name'] ?? '',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Icon(Icons.class_, size: 14, color: Colors.grey.shade600),
                      const SizedBox(width: 4),
                      Text(
                        'Class ${period['class_name']}',
                        style: TextStyle(color: Colors.grey.shade600),
                      ),
                    ],
                  ),
                  if (period['room'] != null) ...[
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        Icon(Icons.room, size: 14, color: Colors.grey.shade600),
                        const SizedBox(width: 4),
                        Text(
                          period['room'],
                          style: TextStyle(color: Colors.grey.shade600),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            // Period indicator
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                'P${index + 1}',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
