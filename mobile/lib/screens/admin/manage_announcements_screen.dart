import 'package:flutter/material.dart';
import '../../config/theme.dart';
import '../../services/api_service.dart';

class ManageAnnouncementsScreen extends StatefulWidget {
  const ManageAnnouncementsScreen({super.key});

  @override
  State<ManageAnnouncementsScreen> createState() => _ManageAnnouncementsScreenState();
}

class _ManageAnnouncementsScreenState extends State<ManageAnnouncementsScreen> {
  final ApiService _api = ApiService();
  List<dynamic> _announcements = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadAnnouncements();
  }

  Future<void> _loadAnnouncements() async {
    try {
      setState(() => _isLoading = true);
      final response = await _api.get('/announcements/all');
      setState(() {
        _announcements = response.data as List<dynamic>;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _createAnnouncement() async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => const CreateAnnouncementDialog(),
    );

    if (result != null) {
      try {
        await _api.post('/announcements/', data: result);
        _loadAnnouncements();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Announcement created'), backgroundColor: Colors.green),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to create'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  Future<void> _deleteAnnouncement(String id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Announcement'),
        content: const Text('Are you sure you want to delete this announcement?'),
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
        await _api.delete('/announcements/$id');
        _loadAnnouncements();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Announcement deleted'), backgroundColor: Colors.green),
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

  Future<void> _togglePin(Map<String, dynamic> announcement) async {
    try {
      await _api.put('/announcements/${announcement['id']}', data: {
        'is_pinned': !(announcement['is_pinned'] ?? false),
      });
      _loadAnnouncements();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to update'), backgroundColor: Colors.red),
        );
      }
    }
  }

  Color _getTypeColor(String type) {
    switch (type) {
      case 'urgent':
        return Colors.red;
      case 'event':
        return Colors.purple;
      case 'holiday':
        return Colors.green;
      default:
        return Colors.blue;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Manage Announcements'),
        backgroundColor: AppTheme.primaryColor,
        foregroundColor: Colors.white,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _createAnnouncement,
        backgroundColor: AppTheme.primaryColor,
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _announcements.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.campaign_outlined, size: 64, color: Colors.grey.shade300),
                      const SizedBox(height: 16),
                      Text('No announcements yet', style: TextStyle(color: Colors.grey.shade600)),
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                        onPressed: _createAnnouncement,
                        icon: const Icon(Icons.add),
                        label: const Text('Create Announcement'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadAnnouncements,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _announcements.length,
                    itemBuilder: (context, index) {
                      final announcement = _announcements[index];
                      final type = announcement['type'] ?? 'general';
                      final color = _getTypeColor(type);
                      final isPinned = announcement['is_pinned'] ?? false;
                      final isActive = announcement['is_active'] ?? true;

                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: Opacity(
                          opacity: isActive ? 1.0 : 0.5,
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                      decoration: BoxDecoration(
                                        color: color.withValues(alpha: 0.1),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Text(
                                        type.toUpperCase(),
                                        style: TextStyle(fontSize: 10, color: color, fontWeight: FontWeight.bold),
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    if (isPinned)
                                      Icon(Icons.push_pin, size: 16, color: Colors.orange.shade700),
                                    const Spacer(),
                                    IconButton(
                                      icon: Icon(
                                        isPinned ? Icons.push_pin : Icons.push_pin_outlined,
                                        color: isPinned ? Colors.orange : Colors.grey,
                                        size: 20,
                                      ),
                                      onPressed: () => _togglePin(announcement),
                                      tooltip: isPinned ? 'Unpin' : 'Pin',
                                    ),
                                    IconButton(
                                      icon: const Icon(Icons.delete_outline, color: Colors.red, size: 20),
                                      onPressed: () => _deleteAnnouncement(announcement['id']),
                                      tooltip: 'Delete',
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  announcement['title'] ?? '',
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  announcement['content'] ?? '',
                                  style: TextStyle(color: Colors.grey.shade700),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                const SizedBox(height: 8),
                                Row(
                                  children: [
                                    Icon(Icons.people_outline, size: 14, color: Colors.grey.shade600),
                                    const SizedBox(width: 4),
                                    Text(
                                      announcement['target_audience'] ?? 'all',
                                      style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                                    ),
                                    const Spacer(),
                                    Text(
                                      'By ${announcement['created_by'] ?? 'Admin'}',
                                      style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}

class CreateAnnouncementDialog extends StatefulWidget {
  const CreateAnnouncementDialog({super.key});

  @override
  State<CreateAnnouncementDialog> createState() => _CreateAnnouncementDialogState();
}

class _CreateAnnouncementDialogState extends State<CreateAnnouncementDialog> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _contentController = TextEditingController();
  String _type = 'general';
  String _targetAudience = 'all';
  bool _isPinned = false;

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Create Announcement'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: _titleController,
                decoration: const InputDecoration(labelText: 'Title*'),
                validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _contentController,
                decoration: const InputDecoration(labelText: 'Content*'),
                maxLines: 4,
                validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _type,
                decoration: const InputDecoration(labelText: 'Type'),
                items: const [
                  DropdownMenuItem(value: 'general', child: Text('General')),
                  DropdownMenuItem(value: 'urgent', child: Text('Urgent')),
                  DropdownMenuItem(value: 'event', child: Text('Event')),
                  DropdownMenuItem(value: 'holiday', child: Text('Holiday')),
                ],
                onChanged: (v) => setState(() => _type = v ?? 'general'),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _targetAudience,
                decoration: const InputDecoration(labelText: 'Target Audience'),
                items: const [
                  DropdownMenuItem(value: 'all', child: Text('Everyone')),
                  DropdownMenuItem(value: 'students', child: Text('Students Only')),
                  DropdownMenuItem(value: 'teachers', child: Text('Teachers Only')),
                  DropdownMenuItem(value: 'parents', child: Text('Parents Only')),
                ],
                onChanged: (v) => setState(() => _targetAudience = v ?? 'all'),
              ),
              const SizedBox(height: 16),
              SwitchListTile(
                title: const Text('Pin to top'),
                value: _isPinned,
                onChanged: (v) => setState(() => _isPinned = v),
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
                'title': _titleController.text,
                'content': _contentController.text,
                'type': _type,
                'target_audience': _targetAudience,
                'is_pinned': _isPinned,
              });
            }
          },
          child: const Text('Create'),
        ),
      ],
    );
  }
}
