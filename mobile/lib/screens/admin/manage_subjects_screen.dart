import 'package:flutter/material.dart';
import '../../config/theme.dart';
import '../../services/api_service.dart';

class ManageSubjectsScreen extends StatefulWidget {
  const ManageSubjectsScreen({super.key});

  @override
  State<ManageSubjectsScreen> createState() => _ManageSubjectsScreenState();
}

class _ManageSubjectsScreenState extends State<ManageSubjectsScreen> {
  final ApiService _api = ApiService();
  List<dynamic> _subjects = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadSubjects();
  }

  Future<void> _loadSubjects() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });
      final response = await _api.get('/admin/subjects');
      setState(() {
        _subjects = response.data as List<dynamic>;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load subjects';
        _isLoading = false;
      });
    }
  }

  Future<void> _addSubject() async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => const AddSubjectDialog(),
    );

    if (result != null) {
      try {
        await _api.post('/admin/subjects', data: result);
        _loadSubjects();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Subject added successfully'), backgroundColor: Colors.green),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to add subject'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  Future<void> _deleteSubject(String id, String name) async {
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
        await _api.delete('/admin/subjects/$id');
        _loadSubjects();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Subject deactivated'), backgroundColor: Colors.orange),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to delete subject'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Manage Subjects'),
        backgroundColor: AppTheme.primaryColor,
        foregroundColor: Colors.white,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addSubject,
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
                      ElevatedButton(onPressed: _loadSubjects, child: const Text('Retry')),
                    ],
                  ),
                )
              : _subjects.isEmpty
                  ? const Center(child: Text('No subjects found'))
                  : RefreshIndicator(
                      onRefresh: _loadSubjects,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _subjects.length,
                        itemBuilder: (context, index) {
                          final subject = _subjects[index];
                          final isActive = subject['is_active'] ?? true;
                          return Card(
                            margin: const EdgeInsets.only(bottom: 8),
                            child: ListTile(
                              leading: Container(
                                width: 48,
                                height: 48,
                                decoration: BoxDecoration(
                                  color: isActive ? Colors.orange.shade100 : Colors.grey.shade200,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Icon(
                                  Icons.menu_book,
                                  color: isActive ? Colors.orange.shade700 : Colors.grey,
                                ),
                              ),
                              title: Text(
                                subject['name'] ?? '',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: isActive ? null : Colors.grey,
                                ),
                              ),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('Code: ${subject['code']} • Credits: ${subject['credits']}'),
                                  if (subject['description'] != null)
                                    Text(
                                      subject['description'],
                                      style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                ],
                              ),
                              isThreeLine: subject['description'] != null,
                              trailing: isActive
                                  ? IconButton(
                                      icon: const Icon(Icons.delete_outline, color: Colors.red),
                                      onPressed: () => _deleteSubject(subject['id'], subject['name']),
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

class AddSubjectDialog extends StatefulWidget {
  const AddSubjectDialog({super.key});

  @override
  State<AddSubjectDialog> createState() => _AddSubjectDialogState();
}

class _AddSubjectDialogState extends State<AddSubjectDialog> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _codeController = TextEditingController();
  final _descriptionController = TextEditingController();
  int _credits = 1;

  @override
  void dispose() {
    _nameController.dispose();
    _codeController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Add Subject'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(labelText: 'Subject Name*'),
                validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
              ),
              TextFormField(
                controller: _codeController,
                decoration: const InputDecoration(labelText: 'Subject Code*'),
                validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
              ),
              TextFormField(
                controller: _descriptionController,
                decoration: const InputDecoration(labelText: 'Description'),
                maxLines: 2,
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  const Text('Credits: '),
                  const SizedBox(width: 16),
                  DropdownButton<int>(
                    value: _credits,
                    items: [1, 2, 3, 4, 5].map((c) {
                      return DropdownMenuItem(value: c, child: Text('$c'));
                    }).toList(),
                    onChanged: (v) => setState(() => _credits = v ?? 1),
                  ),
                ],
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
                'name': _nameController.text,
                'code': _codeController.text,
                'description': _descriptionController.text.isEmpty ? null : _descriptionController.text,
                'credits': _credits,
              });
            }
          },
          child: const Text('Add'),
        ),
      ],
    );
  }
}
