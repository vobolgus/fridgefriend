import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
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

          final household = households.where((h) => h.isActive).firstOrNull ?? households.first;
          return ListView(
            padding: const EdgeInsets.all(16.0),
            children: [
              Text('Name: ${household.name}', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Text('Invite Code: ${household.inviteCode}'),
              const SizedBox(height: 16),
              Text('Members:', style: Theme.of(context).textTheme.titleMedium),
              ...household.members.map(
                (m) => ListTile(
                  leading: const Icon(Icons.person),
                  title: Text(m.email),
                  subtitle: Text(m.role),
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () {
                  context.pushNamed('activity-log', extra: household.id);
                },
                child: const Text('View Activity'),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  void _showCreateDialog(BuildContext context, WidgetRef ref) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Create'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(hintText: 'Household name'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              final name = controller.text.trim();
              if (name.isEmpty) return;
              Navigator.pop(dialogContext);
              try {
                await ref.read(householdRepositoryProvider).createHousehold(name);
                ref.invalidate(householdsProvider);
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Failed to create: $e')),
                  );
                }
              }
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }

  void _showJoinDialog(BuildContext context, WidgetRef ref) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Join'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(hintText: 'Invite Code'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              final code = controller.text.trim();
              if (code.isEmpty) return;
              Navigator.pop(dialogContext);
              try {
                await ref.read(householdRepositoryProvider).joinHousehold(code);
                ref.invalidate(householdsProvider);
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Failed to join: $e')),
                  );
                }
              }
            },
            child: const Text('Join'),
          ),
        ],
      ),
    );
  }
}
