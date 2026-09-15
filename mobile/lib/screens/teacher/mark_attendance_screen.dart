import 'package:flutter/material.dart';
import '../../config/theme.dart';
import '../../services/api_service.dart';

class MarkAttendanceScreen extends StatefulWidget {
  const MarkAttendanceScreen({super.key});

  @override
  State<MarkAttendanceScreen> createState() => _MarkAttendanceScreenState();
}

class _MarkAttendanceScreenState extends State<MarkAttendanceScreen> {
  final ApiService _api = ApiService();
  List<dynamic> _students = [];
  Map<String, String> _attendance = {}; // studentId -> status
  bool _isLoading = true;
  bool _isSaving = false;
  String? _error;
  DateTime _selectedDate = DateTime.now();

  @override
  void initState() {
    super.initState();
    _loadStudents();
  }

  Future<void> _loadStudents() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });
      final response = await _api.get('/teachers/me/students');
      final students = response.data as List<dynamic>;
      setState(() {
        _students = students;
        // Initialize all as present by default
        for (var student in students) {
          _attendance[student['id']] = 'present';
        }
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load students';
        _isLoading = false;
      });
    }
  }

  Future<void> _saveAttendance() async {
    if (_students.isEmpty) return;

    setState(() => _isSaving = true);

    try {
      final requests = _students.map((student) => {
        'student_id': student['id'],
        'record_date': _selectedDate.toIso8601String().split('T')[0],
        'status': _attendance[student['id']] ?? 'present',
      }).toList();

      await _api.post('/teachers/attendance/mark-bulk', data: requests);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Attendance marked for ${_students.length} students'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to save attendance'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mark Attendance'),
        backgroundColor: AppTheme.primaryColor,
        foregroundColor: Colors.white,
        actions: [
          if (_students.isNotEmpty)
            TextButton(
              onPressed: _isSaving ? null : _saveAttendance,
              child: _isSaving
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Text('Save', style: TextStyle(color: Colors.white)),
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(_error!),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadStudents,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : Column(
                  children: [
                    _buildDateSelector(),
                    _buildQuickActions(),
                    Expanded(child: _buildStudentsList()),
                  ],
                ),
    );
  }

  Widget _buildDateSelector() {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.grey.shade100,
      child: Row(
        children: [
          const Icon(Icons.calendar_today, size: 20),
          const SizedBox(width: 12),
          Text(
            '${_selectedDate.day}/${_selectedDate.month}/${_selectedDate.year}',
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
          ),
          const Spacer(),
          TextButton(
            onPressed: () async {
              final date = await showDatePicker(
                context: context,
                initialDate: _selectedDate,
                firstDate: DateTime.now().subtract(const Duration(days: 30)),
                lastDate: DateTime.now(),
              );
              if (date != null) {
                setState(() => _selectedDate = date);
              }
            },
            child: const Text('Change'),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActions() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Expanded(
            child: OutlinedButton.icon(
              onPressed: () {
                setState(() {
                  for (var student in _students) {
                    _attendance[student['id']] = 'present';
                  }
                });
              },
              icon: const Icon(Icons.check_circle, color: Colors.green),
              label: const Text('All Present'),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: OutlinedButton.icon(
              onPressed: () {
                setState(() {
                  for (var student in _students) {
                    _attendance[student['id']] = 'absent';
                  }
                });
              },
              icon: const Icon(Icons.cancel, color: Colors.red),
              label: const Text('All Absent'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStudentsList() {
    if (_students.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.people, size: 64, color: Colors.grey.shade400),
            const SizedBox(height: 16),
            Text(
              'No students assigned',
              style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      itemCount: _students.length,
      itemBuilder: (context, index) {
        final student = _students[index];
        final studentId = student['id'];
        final status = _attendance[studentId] ?? 'present';

        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                CircleAvatar(
                  backgroundColor: AppTheme.primaryColor,
                  child: Text(
                    '${student['first_name'][0]}${student['last_name'][0]}',
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${student['first_name']} ${student['last_name']}',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      Text(
                        student['admission_number'] ?? '',
                        style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                      ),
                    ],
                  ),
                ),
                _buildStatusChip('P', 'present', status, studentId, Colors.green),
                const SizedBox(width: 4),
                _buildStatusChip('A', 'absent', status, studentId, Colors.red),
                const SizedBox(width: 4),
                _buildStatusChip('L', 'late', status, studentId, Colors.orange),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildStatusChip(
    String label,
    String value,
    String currentStatus,
    String studentId,
    Color color,
  ) {
    final isSelected = currentStatus == value;
    return GestureDetector(
      onTap: () {
        setState(() {
          _attendance[studentId] = value;
        });
      },
      child: Container(
        width: 32,
        height: 32,
        decoration: BoxDecoration(
          color: isSelected ? color : Colors.grey.shade200,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              color: isSelected ? Colors.white : Colors.grey.shade600,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
        ),
      ),
    );
  }
}
