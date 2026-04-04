import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/features/households/presentation/providers.dart';

class ActivityLogScreen extends ConsumerWidget {
  final String householdId;

  const ActivityLogScreen({super.key, required this.householdId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final activityAsync = ref.watch(activityLogProvider(householdId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Activity Log'),
      ),
      body: activityAsync.when(
        data: (events) {
          if (events.isEmpty) {
            return const Center(child: Text('No activity found.'));
          }

          return ListView.builder(
            itemCount: events.length,
            itemBuilder: (context, index) {
              final event = events[index];
              final action = event['action'] as String? ?? 'Unknown';
              final userId = event['user_id'] as String? ?? 'Unknown User';
              final timestampStr = event['created_at'] as String?;
              final timestamp = timestampStr != null ? DateTime.tryParse(timestampStr) : null;
              
              final newState = event['new_state'] as Map<String, dynamic>?;
              final previousState = event['previous_state'] as Map<String, dynamic>?;
              final itemName = (newState?['displayName'] ?? newState?['display_name']) ?? 
                               (previousState?['displayName'] ?? previousState?['display_name']) ?? 
                               'Unknown Item';

              return ListTile(
                leading: const Icon(Icons.history),
                title: Text('$action on $itemName'),
                subtitle: Text('By $userId${timestamp != null ? ' at ${timestamp.toLocal()}' : ''}'),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error loading activity: $err')),
      ),
    );
  }
}
