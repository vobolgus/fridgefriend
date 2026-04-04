import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/providers.dart';
import 'providers.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notificationsEnabledAsync = ref.watch(notificationsEnabledProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          notificationsEnabledAsync.when(
            data: (enabled) => SwitchListTile(
              title: const Text('Push Notifications'),
              subtitle: const Text('Reminders for expiring items'),
              value: enabled,
              onChanged: (val) {
                ref.read(notificationsEnabledProvider.notifier).toggle(val);
              },
            ),
            loading: () => const ListTile(
              title: Text('Push Notifications'),
              subtitle: Text('Reminders for expiring items'),
              trailing: CircularProgressIndicator(),
            ),
            error: (err, stack) => ListTile(
              title: const Text('Push Notifications'),
              subtitle: Text('Error loading preferences: $err'),
            ),
          ),
          const Divider(),
          ListTile(
            title: const Text('Household Management'),
            leading: const Icon(Icons.home),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              context.push('/household');
            },
          ),
          const Divider(),
          ListTile(
            title: const Text('Sign Out'),
            leading: const Icon(Icons.logout, color: Colors.red),
            textColor: Colors.red,
            onTap: () async {
              await ref.read(authServiceProvider).signOut();
            },
          ),
          const Divider(),
          const ListTile(
            title: Text('App Version'),
            trailing: Text('1.0.0'),
          ),
        ],
      ),
    );
  }
}
