import 'package:flutter/material.dart';
import '../../config/theme.dart';
import '../../services/api_service.dart';

class ManageStudentsScreen extends StatefulWidget {
  const ManageStudentsScreen({super.key});

  @override
  State<ManageStudentsScreen> createState() => _ManageStudentsScreenState();
}

class _ManageStudentsScreenState extends State<ManageStudentsScreen> {
  final ApiService _api = ApiService();
  List<dynamic> _students = [];
  bool _isLoading = true;
  String? _error;

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
      final response = await _api.get('/admin/students');
      setState(() {
        _students = response.data as List<dynamic>;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load students';
        _isLoading = false;
      });
    }
  }

  Future<void> _addStudent() async {
    final result = await showDialog<Map<String, String>>(
      context: context,
      builder: (context) => const AddStudentDialog(),
    );

    if (result != null) {
      try {
        await _api.post('/admin/students', data: result);
        _loadStudents();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Student added successfully'), backgroundColor: Colors.green),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to add student'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  Future<void> _deleteStudent(String id, String name) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Delete'),
        content: Text('Are you sure you want to deactivate $name?'),
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
        await _api.delete('/admin/students/$id');
        _loadStudents();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Student deactivated'), backgroundColor: Colors.orange),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to delete student'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Manage Students'),
        backgroundColor: AppTheme.primaryColor,
        foregroundColor: Colors.white,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addStudent,
        backgroundColor: AppTheme.primaryColor,
        child: const Icon(Icons.add, color: Colors.white),
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
                      ElevatedButton(onPressed: _loadStudents, child: const Text('Retry')),
                    ],
                  ),
                )
              : _students.isEmpty
                  ? const Center(child: Text('No students found'))
                  : RefreshIndicator(
                      onRefresh: _loadStudents,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _students.length,
                        itemBuilder: (context, index) {
                          final student = _students[index];
                          final isActive = student['is_active'] ?? true;
                          return Card(
                            margin: const EdgeInsets.only(bottom: 8),
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor: isActive ? Colors.blue : Colors.grey,
                                child: Text(
                                  '${student['first_name'][0]}${student['last_name'][0]}',
                                  style: const TextStyle(color: Colors.white),
                                ),
                              ),
                              title: Text(
                                '${student['first_name']} ${student['last_name']}',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: isActive ? null : Colors.grey,
                                ),
                              ),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(student['admission_number'] ?? ''),
                                  Text(
                                    student['email'] ?? '',
                                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                                  ),
                                ],
                              ),
                              isThreeLine: true,
                              trailing: isActive
                                  ? IconButton(
                                      icon: const Icon(Icons.delete_outline, color: Colors.red),
                                      onPressed: () => _deleteStudent(
                                        student['id'],
                                        '${student['first_name']} ${student['last_name']}',
                                      ),
                                    )
                                  : const Chip(label: Text('Inactive', style: TextStyle(fontSize: 10))),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}

class AddStudentDialog extends StatefulWidget {
  const AddStudentDialog({super.key});

  @override
  State<AddStudentDialog> createState() => _AddStudentDialogState();
}

class _AddStudentDialogState extends State<AddStudentDialog> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _admissionController = TextEditingController();
  final _rollController = TextEditingController();
  final _parentNameController = TextEditingController();
  final _parentPhoneController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _firstNameController.dispose();
    _lastNameController.dispose();
    _admissionController.dispose();
    _rollController.dispose();
    _parentNameController.dispose();
    _parentPhoneController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Add Student'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: _firstNameController,
                decoration: const InputDecoration(labelText: 'First Name*'),
                validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
              ),
              TextFormField(
                controller: _lastNameController,
                decoration: const InputDecoration(labelText: 'Last Name*'),
                validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
              ),
              TextFormField(
                controller: _emailController,
                decoration: const InputDecoration(labelText: 'Email*'),
                validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
              ),
              TextFormField(
                controller: _passwordController,
                decoration: const InputDecoration(labelText: 'Password*'),
                obscureText: true,
                validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
              ),
              TextFormField(
                controller: _admissionController,
                decoration: const InputDecoration(labelText: 'Admission Number*'),
                validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
              ),
              TextFormField(
                controller: _rollController,
                decoration: const InputDecoration(labelText: 'Roll Number'),
              ),
              TextFormField(
                controller: _parentNameController,
                decoration: const InputDecoration(labelText: 'Parent Name'),
              ),
              TextFormField(
                controller: _parentPhoneController,
                decoration: const InputDecoration(labelText: 'Parent Phone'),
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
                'email': _emailController.text,
                'password': _passwordController.text,
                'first_name': _firstNameController.text,
                'last_name': _lastNameController.text,
                'admission_number': _admissionController.text,
                'roll_number': _rollController.text,
                'parent_name': _parentNameController.text,
                'parent_phone': _parentPhoneController.text,
              });
            }
          },
          child: const Text('Add'),
        ),
      ],
    );
  }
}
