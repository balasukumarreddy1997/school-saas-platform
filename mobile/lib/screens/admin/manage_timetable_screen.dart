import 'package:flutter/material.dart';
import '../../config/theme.dart';
import '../../services/api_service.dart';

class ManageTimetableScreen extends StatefulWidget {
  const ManageTimetableScreen({super.key});

  @override
  State<ManageTimetableScreen> createState() => _ManageTimetableScreenState();
}

class _ManageTimetableScreenState extends State<ManageTimetableScreen> {
  final ApiService _api = ApiService();
  List<dynamic> _timetable = [];
  List<dynamic> _subjects = [];
  List<dynamic> _teachers = [];
  bool _isLoading = true;
  String _selectedClass = '10-A';

  final List<String> _classes = ['10-A', '10-B', '9-A', '9-B', '8-A', '8-B'];
  final List<String> _days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      setState(() => _isLoading = true);

      final responses = await Future.wait([
        _api.get('/timetable/all?class_name=$_selectedClass'),
        _api.get('/subjects/'),
        _api.get('/admin/teachers'),
      ]);

      setState(() {
        _timetable = responses[0].data as List<dynamic>;
        _subjects = responses[1].data as List<dynamic>;
        _teachers = responses[2].data as List<dynamic>;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _addEntry() async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => AddTimetableEntryDialog(
        className: _selectedClass,
        subjects: _subjects,
        teachers: _teachers,
      ),
    );

    if (result != null) {
      try {
        await _api.post('/timetable/', data: result);
        _loadData();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Entry added'), backgroundColor: Colors.green),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to add entry'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  Future<void> _deleteEntry(String id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Entry'),
        content: const Text('Are you sure you want to delete this timetable entry?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      try {
        await _api.delete('/timetable/$id');
        _loadData();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Entry deleted'), backgroundColor: Colors.green),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to delete'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Manage Timetable'),
        backgroundColor: AppTheme.primaryColor,
        foregroundColor: Colors.white,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addEntry,
        backgroundColor: AppTheme.primaryColor,
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: Column(
        children: [
          // Class selector
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.grey.shade100,
            child: Row(
              children: [
                const Text('Class: ', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(width: 8),
                Expanded(
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: _classes.map((c) {
                        final isSelected = c == _selectedClass;
                        return Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: ChoiceChip(
                            label: Text(c),
                            selected: isSelected,
                            onSelected: (selected) {
                              if (selected) {
                                setState(() => _selectedClass = c);
                                _loadData();
                              }
                            },
                            selectedColor: AppTheme.primaryColor,
                            labelStyle: TextStyle(
                              color: isSelected ? Colors.white : Colors.black,
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ),
              ],
            ),
          ),
          // Timetable list
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _timetable.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.schedule, size: 64, color: Colors.grey.shade300),
                            const SizedBox(height: 16),
                            Text(
                              'No timetable entries for $_selectedClass',
                              style: TextStyle(color: Colors.grey.shade600),
                            ),
                            const SizedBox(height: 8),
                            ElevatedButton.icon(
                              onPressed: _addEntry,
                              icon: const Icon(Icons.add),
                              label: const Text('Add Entry'),
                            ),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _loadData,
                        child: ListView(
                          padding: const EdgeInsets.all(16),
                          children: _days.map((day) {
                            final dayEntries = _timetable
                                .where((e) => e['day_name'] == day)
                                .toList();
                            if (dayEntries.isEmpty) return const SizedBox.shrink();
                            return _buildDaySection(day, dayEntries);
                          }).toList(),
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildDaySection(String day, List<dynamic> entries) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Text(
            day,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
        ),
        ...entries.map((entry) => Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                leading: Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: Colors.blue.shade100,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        entry['start_time'] ?? '',
                        style: TextStyle(fontSize: 10, color: Colors.blue.shade700),
                      ),
                      Text(
                        entry['end_time'] ?? '',
                        style: TextStyle(fontSize: 10, color: Colors.blue.shade700),
                      ),
                    ],
                  ),
                ),
                title: Text(entry['subject_name'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (entry['teacher_name'] != null)
                      Text('Teacher: ${entry['teacher_name']}'),
                    if (entry['room'] != null)
                      Text('Room: ${entry['room']}'),
                  ],
                ),
                trailing: IconButton(
                  icon: const Icon(Icons.delete_outline, color: Colors.red),
                  onPressed: () => _deleteEntry(entry['id']),
                ),
              ),
            )),
        const SizedBox(height: 16),
      ],
    );
  }
}

class AddTimetableEntryDialog extends StatefulWidget {
  final String className;
  final List<dynamic> subjects;
  final List<dynamic> teachers;

  const AddTimetableEntryDialog({
    super.key,
    required this.className,
    required this.subjects,
    required this.teachers,
  });

  @override
  State<AddTimetableEntryDialog> createState() => _AddTimetableEntryDialogState();
}

class _AddTimetableEntryDialogState extends State<AddTimetableEntryDialog> {
  final _formKey = GlobalKey<FormState>();
  String? _subjectId;
  String? _teacherId;
  int _dayOfWeek = 0;
  TimeOfDay _startTime = const TimeOfDay(hour: 9, minute: 0);
  TimeOfDay _endTime = const TimeOfDay(hour: 9, minute: 45);
  final _roomController = TextEditingController();

  final List<String> _days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  @override
  void dispose() {
    _roomController.dispose();
    super.dispose();
  }

  String _formatTime(TimeOfDay time) {
    return '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Add Entry for ${widget.className}'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Day
              DropdownButtonFormField<int>(
                value: _dayOfWeek,
                decoration: const InputDecoration(labelText: 'Day'),
                items: _days.asMap().entries.map((e) {
                  return DropdownMenuItem(value: e.key, child: Text(e.value));
                }).toList(),
                onChanged: (v) => setState(() => _dayOfWeek = v ?? 0),
              ),
              const SizedBox(height: 16),
              // Subject
              DropdownButtonFormField<String>(
                value: _subjectId,
                decoration: const InputDecoration(labelText: 'Subject*'),
                items: widget.subjects.map((s) {
                  return DropdownMenuItem(
                    value: s['id'] as String,
                    child: Text(s['name'] as String),
                  );
                }).toList(),
                onChanged: (v) => setState(() => _subjectId = v),
                validator: (v) => v == null ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              // Teacher
              DropdownButtonFormField<String>(
                value: _teacherId,
                decoration: const InputDecoration(labelText: 'Teacher'),
                items: [
                  const DropdownMenuItem(value: null, child: Text('-- Select --')),
                  ...widget.teachers.map((t) {
                    return DropdownMenuItem(
                      value: t['id'] as String,
                      child: Text(t['name'] as String),
                    );
                  }),
                ],
                onChanged: (v) => setState(() => _teacherId = v),
              ),
              const SizedBox(height: 16),
              // Times
              Row(
                children: [
                  Expanded(
                    child: InkWell(
                      onTap: () async {
                        final picked = await showTimePicker(
                          context: context,
                          initialTime: _startTime,
                        );
                        if (picked != null) setState(() => _startTime = picked);
                      },
                      child: InputDecorator(
                        decoration: const InputDecoration(labelText: 'Start'),
                        child: Text(_formatTime(_startTime)),
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: InkWell(
                      onTap: () async {
                        final picked = await showTimePicker(
                          context: context,
                          initialTime: _endTime,
                        );
                        if (picked != null) setState(() => _endTime = picked);
                      },
                      child: InputDecorator(
                        decoration: const InputDecoration(labelText: 'End'),
                        child: Text(_formatTime(_endTime)),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              // Room
              TextFormField(
                controller: _roomController,
                decoration: const InputDecoration(labelText: 'Room'),
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
        ElevatedButton(
          onPressed: () {
            if (_formKey.currentState!.validate()) {
              Navigator.pop(context, {
                'class_name': widget.className,
                'subject_id': _subjectId,
                'teacher_id': _teacherId,
                'day_of_week': _dayOfWeek,
                'start_time': _formatTime(_startTime),
                'end_time': _formatTime(_endTime),
                'room': _roomController.text.isEmpty ? null : _roomController.text,
              });
            }
          },
          child: const Text('Add'),
        ),
      ],
    );
  }
}
