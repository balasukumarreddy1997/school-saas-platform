import 'package:flutter/material.dart';
import '../../config/theme.dart';
import '../../services/api_service.dart';

class ManageFeesScreen extends StatefulWidget {
  const ManageFeesScreen({super.key});

  @override
  State<ManageFeesScreen> createState() => _ManageFeesScreenState();
}

class _ManageFeesScreenState extends State<ManageFeesScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final ApiService _api = ApiService();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Fee Management'),
        backgroundColor: AppTheme.primaryColor,
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: const [
            Tab(text: 'Structures'),
            Tab(text: 'Student Fees'),
            Tab(text: 'Summary'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          FeeStructuresTab(),
          StudentFeesTab(),
          FeeSummaryTab(),
        ],
      ),
    );
  }
}

class FeeStructuresTab extends StatefulWidget {
  const FeeStructuresTab({super.key});

  @override
  State<FeeStructuresTab> createState() => _FeeStructuresTabState();
}

class _FeeStructuresTabState extends State<FeeStructuresTab> {
  final ApiService _api = ApiService();
  List<dynamic> _structures = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadStructures();
  }

  Future<void> _loadStructures() async {
    try {
      setState(() => _isLoading = true);
      final response = await _api.get('/fees/structures');
      setState(() {
        _structures = response.data as List<dynamic>;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _addStructure() async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => const AddFeeStructureDialog(),
    );

    if (result != null) {
      try {
        await _api.post('/fees/structures', data: result);
        _loadStructures();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Fee structure added'), backgroundColor: Colors.green),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to add'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      floatingActionButton: FloatingActionButton(
        onPressed: _addStructure,
        backgroundColor: AppTheme.primaryColor,
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _structures.isEmpty
              ? const Center(child: Text('No fee structures defined'))
              : RefreshIndicator(
                  onRefresh: _loadStructures,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _structures.length,
                    itemBuilder: (context, index) {
                      final structure = _structures[index];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          leading: Container(
                            width: 48,
                            height: 48,
                            decoration: BoxDecoration(
                              color: Colors.green.shade100,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Icon(Icons.receipt_long, color: Colors.green.shade700),
                          ),
                          title: Text(
                            structure['name'] ?? '',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          subtitle: Text(
                            '₹${structure['amount']} • ${structure['frequency']}',
                          ),
                          trailing: Text(
                            structure['academic_year'] ?? '',
                            style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}

class StudentFeesTab extends StatefulWidget {
  const StudentFeesTab({super.key});

  @override
  State<StudentFeesTab> createState() => _StudentFeesTabState();
}

class _StudentFeesTabState extends State<StudentFeesTab> {
  final ApiService _api = ApiService();
  List<dynamic> _fees = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadFees();
  }

  Future<void> _loadFees() async {
    try {
      setState(() => _isLoading = true);
      final response = await _api.get('/fees/all-students');
      setState(() {
        _fees = response.data as List<dynamic>;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _recordPayment(Map<String, dynamic> fee) async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => RecordPaymentDialog(
        balance: (fee['balance'] as num).toDouble(),
      ),
    );

    if (result != null) {
      try {
        result['student_fee_id'] = fee['id'];
        await _api.post('/fees/payment', data: result);
        _loadFees();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Payment recorded'), backgroundColor: Colors.green),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to record payment'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return _isLoading
        ? const Center(child: CircularProgressIndicator())
        : _fees.isEmpty
            ? const Center(child: Text('No fees assigned'))
            : RefreshIndicator(
                onRefresh: _loadFees,
                child: ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _fees.length,
                  itemBuilder: (context, index) {
                    final fee = _fees[index];
                    final status = fee['status'] ?? 'pending';
                    final color = status == 'paid'
                        ? Colors.green
                        : status == 'partial'
                            ? Colors.orange
                            : Colors.red;

                    return Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        fee['student_name'] ?? '',
                                        style: const TextStyle(fontWeight: FontWeight.bold),
                                      ),
                                      Text(
                                        fee['admission_number'] ?? '',
                                        style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                                      ),
                                    ],
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: color.withValues(alpha: 0.1),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text(
                                    status.toUpperCase(),
                                    style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(fee['fee_name'] ?? ''),
                                Text('Due: ${fee['due_date']}'),
                              ],
                            ),
                            const Divider(),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('Total: ₹${fee['amount']}'),
                                    Text('Paid: ₹${fee['amount_paid']}', style: const TextStyle(color: Colors.green)),
                                    Text('Balance: ₹${fee['balance']}', style: TextStyle(color: color)),
                                  ],
                                ),
                                if (status != 'paid')
                                  ElevatedButton(
                                    onPressed: () => _recordPayment(fee),
                                    style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                                    child: const Text('Pay', style: TextStyle(color: Colors.white)),
                                  ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              );
  }
}

class FeeSummaryTab extends StatefulWidget {
  const FeeSummaryTab({super.key});

  @override
  State<FeeSummaryTab> createState() => _FeeSummaryTabState();
}

class _FeeSummaryTabState extends State<FeeSummaryTab> {
  final ApiService _api = ApiService();
  Map<String, dynamic>? _summary;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSummary();
  }

  Future<void> _loadSummary() async {
    try {
      setState(() => _isLoading = true);
      final response = await _api.get('/fees/summary');
      setState(() {
        _summary = response.data as Map<String, dynamic>;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return _isLoading
        ? const Center(child: CircularProgressIndicator())
        : RefreshIndicator(
            onRefresh: _loadSummary,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _buildSummaryCard('Total Fees', '₹${_summary?['total_fees'] ?? 0}', Colors.blue, Icons.account_balance),
                _buildSummaryCard('Collected', '₹${_summary?['total_paid'] ?? 0}', Colors.green, Icons.check_circle),
                _buildSummaryCard('Pending', '₹${_summary?['total_pending'] ?? 0}', Colors.orange, Icons.pending),
                _buildSummaryCard('Overdue', '${_summary?['overdue_count'] ?? 0} students', Colors.red, Icons.warning),
              ],
            ),
          );
  }

  Widget _buildSummaryCard(String title, String value, Color color, IconData icon) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: color, size: 28),
            ),
            const SizedBox(width: 16),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: TextStyle(color: Colors.grey.shade600)),
                Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class AddFeeStructureDialog extends StatefulWidget {
  const AddFeeStructureDialog({super.key});

  @override
  State<AddFeeStructureDialog> createState() => _AddFeeStructureDialogState();
}

class _AddFeeStructureDialogState extends State<AddFeeStructureDialog> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _amountController = TextEditingController();
  final _descController = TextEditingController();
  String _frequency = 'monthly';
  String _academicYear = '2026-2027';

  @override
  void dispose() {
    _nameController.dispose();
    _amountController.dispose();
    _descController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Add Fee Structure'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(labelText: 'Fee Name*'),
                validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
              ),
              TextFormField(
                controller: _amountController,
                decoration: const InputDecoration(labelText: 'Amount*', prefixText: '₹ '),
                keyboardType: TextInputType.number,
                validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
              ),
              TextFormField(
                controller: _descController,
                decoration: const InputDecoration(labelText: 'Description'),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _frequency,
                decoration: const InputDecoration(labelText: 'Frequency'),
                items: const [
                  DropdownMenuItem(value: 'monthly', child: Text('Monthly')),
                  DropdownMenuItem(value: 'quarterly', child: Text('Quarterly')),
                  DropdownMenuItem(value: 'yearly', child: Text('Yearly')),
                  DropdownMenuItem(value: 'one_time', child: Text('One Time')),
                ],
                onChanged: (v) => setState(() => _frequency = v ?? 'monthly'),
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
                'amount': double.parse(_amountController.text),
                'description': _descController.text.isEmpty ? null : _descController.text,
                'frequency': _frequency,
                'academic_year': _academicYear,
              });
            }
          },
          child: const Text('Add'),
        ),
      ],
    );
  }
}

class RecordPaymentDialog extends StatefulWidget {
  final double balance;

  const RecordPaymentDialog({super.key, required this.balance});

  @override
  State<RecordPaymentDialog> createState() => _RecordPaymentDialogState();
}

class _RecordPaymentDialogState extends State<RecordPaymentDialog> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _transactionIdController = TextEditingController();
  String _paymentMethod = 'cash';

  @override
  void initState() {
    super.initState();
    _amountController.text = widget.balance.toString();
  }

  @override
  void dispose() {
    _amountController.dispose();
    _transactionIdController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Record Payment'),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextFormField(
              controller: _amountController,
              decoration: InputDecoration(
                labelText: 'Amount*',
                prefixText: '₹ ',
                helperText: 'Balance: ₹${widget.balance}',
              ),
              keyboardType: TextInputType.number,
              validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _paymentMethod,
              decoration: const InputDecoration(labelText: 'Payment Method'),
              items: const [
                DropdownMenuItem(value: 'cash', child: Text('Cash')),
                DropdownMenuItem(value: 'upi', child: Text('UPI')),
                DropdownMenuItem(value: 'card', child: Text('Card')),
                DropdownMenuItem(value: 'bank_transfer', child: Text('Bank Transfer')),
              ],
              onChanged: (v) => setState(() => _paymentMethod = v ?? 'cash'),
            ),
            if (_paymentMethod != 'cash')
              TextFormField(
                controller: _transactionIdController,
                decoration: const InputDecoration(labelText: 'Transaction ID'),
              ),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
        ElevatedButton(
          onPressed: () {
            if (_formKey.currentState!.validate()) {
              Navigator.pop(context, {
                'amount': double.parse(_amountController.text),
                'payment_method': _paymentMethod,
                'transaction_id': _transactionIdController.text.isEmpty ? null : _transactionIdController.text,
              });
            }
          },
          child: const Text('Record'),
        ),
      ],
    );
  }
}
