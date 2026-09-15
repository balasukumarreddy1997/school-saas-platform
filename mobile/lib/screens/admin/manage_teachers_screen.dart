import 'package:flutter/material.dart';
import '../../config/theme.dart';
import '../../services/api_service.dart';

class ManageTeachersScreen extends StatefulWidget {
  const ManageTeachersScreen({super.key});

  @override
  State<ManageTeachersScreen> createState() => _ManageTeachersScreenState();
}

class _ManageTeachersScreenState extends State<ManageTeachersScreen> {
  final ApiService _api = ApiService();
  List<dynamic> _teachers = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadTeachers();
  }

  Future<void> _loadTeachers() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });
      final response = await _api.get('/admin/teachers');
      setState(() {
        _teachers = response.data as List<dynamic>;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load teachers';
        _isLoading = false;
      });
    }
  }

  Future<void> _addTeacher() async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => const AddTeacherDialog(),
    );

    if (result != null) {
      try {
        await _api.post('/admin/teachers', data: result);
        _loadTeachers();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Teacher added successfully'), backgroundColor: Colors.green),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to add teacher'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  Future<void> _deleteTeacher(String id, String name) async {
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
        await _api.delete('/admin/teachers/$id');
        _loadTeachers();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Teacher deactivated'), backgroundColor: Colors.orange),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to delete teacher'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Manage Teachers'),
        backgroundColor: AppTheme.primaryColor,
        foregroundColor: Colors.white,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addTeacher,
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
                      ElevatedButton(onPressed: _loadTeachers, child: const Text('Retry')),
                    ],
                  ),
                )
              : _teachers.isEmpty
                  ? const Center(child: Text('No teachers found'))
                  : RefreshIndicator(
                      onRefresh: _loadTeachers,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _teachers.length,
                        itemBuilder: (context, index) {
                          final teacher = _teachers[index];
                          final isActive = teacher['is_active'] ?? true;
                          return Card(
                            margin: const EdgeInsets.only(bottom: 8),
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor: isActive ? Colors.green : Colors.grey,
                                child: Text(
                                  '${teacher['first_name'][0]}${teacher['last_name'][0]}',
                                  style: const TextStyle(color: Colors.white),
                                ),
                              ),
                              title: Text(
                                '${teacher['first_name']} ${teacher['last_name']}',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: isActive ? null : Colors.grey,
                                ),
                              ),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('${teacher['employee_id']} • ${teacher['department'] ?? 'N/A'}'),
                                  Text(
                                    teacher['email'] ?? '',
                                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                                  ),
                                ],
                              ),
                              isThreeLine: true,
                              trailing: isActive
                                  ? IconButton(
                                      icon: const Icon(Icons.delete_outline, color: Colors.red),
                                      onPressed: () => _deleteTeacher(
                                        teacher['id'],
                                        '${teacher['first_name']} ${teacher['last_name']}',
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

class AddTeacherDialog extends StatefulWidget {
  const AddTeacherDialog({super.key});

  @override
  State<AddTeacherDialog> createState() => _AddTeacherDialogState();
}

class _AddTeacherDialogState extends State<AddTeacherDialog> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _employeeIdController = TextEditingController();
  final _departmentController = TextEditingController();
  final _qualificationController = TextEditingController();
  bool _isClassTeacher = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _firstNameController.dispose();
    _lastNameController.dispose();
    _employeeIdController.dispose();
    _departmentController.dispose();
    _qualificationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Add Teacher'),
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
                controller: _employeeIdController,
                decoration: const InputDecoration(labelText: 'Employee ID*'),
                validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
              ),
              TextFormField(
                controller: _departmentController,
                decoration: const InputDecoration(labelText: 'Department'),
              ),
              TextFormField(
                controller: _qualificationController,
                decoration: const InputDecoration(labelText: 'Qualification'),
              ),
              CheckboxListTile(
                title: const Text('Class Teacher'),
                value: _isClassTeacher,
                onChanged: (v) => setState(() => _isClassTeacher = v ?? false),
                contentPadding: EdgeInsets.zero,
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
                'employee_id': _employeeIdController.text,
                'department': _departmentController.text,
                'qualification': _qualificationController.text,
                'is_class_teacher': _isClassTeacher,
              });
            }
          },
          child: const Text('Add'),
        ),
      ],
    );
  }
}
