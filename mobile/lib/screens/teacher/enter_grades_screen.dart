import 'package:flutter/material.dart';
import '../../config/theme.dart';
import '../../services/api_service.dart';

class EnterGradesScreen extends StatefulWidget {
  const EnterGradesScreen({super.key});

  @override
  State<EnterGradesScreen> createState() => _EnterGradesScreenState();
}

class _EnterGradesScreenState extends State<EnterGradesScreen> {
  final ApiService _api = ApiService();
  List<dynamic> _students = [];
  List<dynamic> _subjects = [];
  String? _selectedSubjectId;
  String _examName = '';
  final Map<String, TextEditingController> _marksControllers = {};
  bool _isLoading = true;
  bool _isSaving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void dispose() {
    for (var controller in _marksControllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _loadData() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });

      final dashboardResponse = await _api.get('/teachers/me/dashboard');
      final dashboard = dashboardResponse.data as Map<String, dynamic>;
      final subjects = dashboard['subjects_teaching'] as List<dynamic>? ?? [];

      final studentsResponse = await _api.get('/teachers/me/students');
      final students = studentsResponse.data as List<dynamic>;

      setState(() {
        _subjects = subjects;
        _students = students;
        if (subjects.isNotEmpty) {
          _selectedSubjectId = subjects[0]['subject_id'];
        }
        for (var student in students) {
          _marksControllers[student['id']] = TextEditingController();
        }
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load data';
        _isLoading = false;
      });
    }
  }

  Future<void> _saveGrades() async {
    if (_selectedSubjectId == null || _examName.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select subject and enter exam name')),
      );
      return;
    }

    setState(() => _isSaving = true);

    try {
      int count = 0;
      for (var student in _students) {
        final controller = _marksControllers[student['id']];
        if (controller != null && controller.text.isNotEmpty) {
          final marks = double.tryParse(controller.text);
          if (marks != null) {
            await _api.post('/teachers/results/enter', data: {
              'student_id': student['id'],
              'subject_id': _selectedSubjectId,
              'exam_name': _examName,
              'max_marks': 100.0,
              'marks_obtained': marks,
              'grade': _calculateGrade(marks),
              'academic_year': '2026-2027',
            });
            count++;
          }
        }
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Grades saved for $count students'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to save grades'),
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

  String _calculateGrade(double marks) {
    if (marks >= 90) return 'A+';
    if (marks >= 80) return 'A';
    if (marks >= 70) return 'B+';
    if (marks >= 60) return 'B';
    if (marks >= 50) return 'C';
    if (marks >= 40) return 'D';
    return 'F';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Enter Grades'),
        backgroundColor: AppTheme.primaryColor,
        foregroundColor: Colors.white,
        actions: [
          if (_students.isNotEmpty)
            TextButton(
              onPressed: _isSaving ? null : _saveGrades,
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
                        onPressed: _loadData,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : Column(
                  children: [
                    _buildSubjectSelector(),
                    _buildExamNameField(),
                    Expanded(child: _buildStudentsList()),
                  ],
                ),
    );
  }

  Widget _buildSubjectSelector() {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.grey.shade100,
      child: Row(
        children: [
          const Text('Subject: ', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(width: 12),
          Expanded(
            child: DropdownButton<String>(
              value: _selectedSubjectId,
              isExpanded: true,
              underline: const SizedBox(),
              items: _subjects.map((subject) {
                return DropdownMenuItem<String>(
                  value: subject['subject_id'],
                  child: Text(subject['subject_name'] ?? ''),
                );
              }).toList(),
              onChanged: (value) {
                setState(() => _selectedSubjectId = value);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildExamNameField() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: TextField(
        decoration: const InputDecoration(
          labelText: 'Exam Name',
          hintText: 'e.g., Mid-Term Exam, Unit Test 1',
          border: OutlineInputBorder(),
        ),
        onChanged: (value) => _examName = value,
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
        final controller = _marksControllers[student['id']]!;

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
                SizedBox(
                  width: 80,
                  child: TextField(
                    controller: controller,
                    keyboardType: TextInputType.number,
                    textAlign: TextAlign.center,
                    decoration: const InputDecoration(
                      hintText: 'Marks',
                      border: OutlineInputBorder(),
                      contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                const Text('/100'),
              ],
            ),
          ),
        );
      },
    );
  }
}
