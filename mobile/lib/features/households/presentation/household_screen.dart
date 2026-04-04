import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'providers.dart';

class HouseholdScreen extends ConsumerWidget {
  const HouseholdScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final householdsAsync = ref.watch(householdsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Household Management')),
      body: householdsAsync.when(
        data: (households) {
          if (households.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('You are not in any household.'),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => _showCreateDialog(context, ref),
                    child: const Text('Create Household'),
                  ),
                  TextButton(
                    onPressed: () => _showJoinDialog(context, ref),
                    child: const Text('Join Household'),
                  ),
                ],
              ),
            );
          }

          final household = households.first;
          return ListView(
            padding: const EdgeInsets.all(16.0),
            children: [
              Text('Name: ${household.name}', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Text('Invite Code: ${household.inviteCode}'),
              const SizedBox(height: 16),
              Text('Members:', style: Theme.of(context).textTheme.titleMedium),
              ...household.members.map((m) => ListTile(title: Text(m))),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  void _showCreateDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Create'),
        content: const TextField(decoration: InputDecoration(hintText: 'Name')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }

  void _showJoinDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Join'),
        content: const TextField(decoration: InputDecoration(hintText: 'Invite Code')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Join'),
          ),
        ],
      ),
    );
  }
}
