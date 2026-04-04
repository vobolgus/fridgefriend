import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'providers.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final prefsAsync = ref.watch(notificationPreferencesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          prefsAsync.when(
            data: (prefs) => Column(
              children: [
                SwitchListTile(
                  title: const Text('Push Notifications'),
                  subtitle: const Text('Reminders for expiring items'),
                  value: prefs.enabled,
                  onChanged: (val) {
                    ref.read(notificationPreferencesProvider.notifier).toggleEnabled(val);
                  },
                ),
                ListTile(
                  title: const Text('Remind days before expiry'),
                  trailing: DropdownButton<int>(
                    value: prefs.reminderDaysBefore,
                    items: List.generate(8, (i) => i).map((days) {
                      return DropdownMenuItem(
                        value: days,
                        child: Text(days == 0 ? 'Same day' : '$days day${days > 1 ? 's' : ''}'),
                      );
                    }).toList(growable: false),
                    onChanged: prefs.enabled
                        ? (val) {
                            if (val != null) {
                              ref.read(notificationPreferencesProvider.notifier).setReminderDaysBefore(val);
                            }
                          }
                        : null,
                  ),
                ),
                ListTile(
                  title: const Text('Quiet hours'),
                  subtitle: Text(
                    prefs.quietHoursStart != null && prefs.quietHoursEnd != null
                        ? '${prefs.quietHoursStart!.format(context)} - ${prefs.quietHoursEnd!.format(context)}'
                        : 'Not set',
                  ),
                  trailing: const Icon(Icons.chevron_right),
                  enabled: prefs.enabled,
                  onTap: prefs.enabled
                      ? () async {
                          final start = await showTimePicker(
                            context: context,
                            initialTime: prefs.quietHoursStart ?? const TimeOfDay(hour: 22, minute: 0),
                            helpText: 'Quiet hours start',
                          );
                          if (start == null || !context.mounted) return;
                          final end = await showTimePicker(
                            context: context,
                            initialTime: prefs.quietHoursEnd ?? const TimeOfDay(hour: 8, minute: 0),
                            helpText: 'Quiet hours end',
                          );
                          if (end == null) return;
                          ref.read(notificationPreferencesProvider.notifier).setQuietHours(start, end);
                        }
                      : null,
                ),
              ],
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
              final syncManager = ref.read(syncManagerProvider);
              final pending = await syncManager.pendingMutations();
              if (pending.isNotEmpty) {
                try {
                  await syncManager.flushPendingMutations();
                } catch (_) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Sync pending changes before signing out')),
                    );
                  }
                  return;
                }
              }

              final pushService = ref.read(pushNotificationServiceProvider);
              final apiClient = ref.read(apiClientProvider);
              await pushService.unregisterToken(apiClient);

              final db = ref.read(appDatabaseProvider);
              await db.inventoryDao.clearAll();
              await db.recipeDao.clear();
              await db.mealPlanDao.clear();

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
