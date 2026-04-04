import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'providers.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final prefsAsync = ref.watch(notificationPreferencesProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text(
          'Settings',
          style: TextStyle(
            fontFamily: 'Inter',
            fontWeight: FontWeight.w900,
            fontSize: 24,
            color: AppColors.textPrimary,
          ),
        ),
        backgroundColor: AppColors.navBarBackground,
        elevation: 0,
        centerTitle: false,
      ),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: [
          _buildSectionHeader('PREFERENCES'),
          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
              side: const BorderSide(color: AppColors.divider, width: 1),
            ),
            color: AppColors.surface,
            margin: const EdgeInsets.only(bottom: AppSpacing.xl),
            child: prefsAsync.when(
              data: (prefs) => Column(
                children: [
                  SwitchListTile(
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.lg, vertical: AppSpacing.sm),
                    title: const Text(
                      'Push Notifications',
                      style: TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w800,
                          color: AppColors.textPrimary),
                    ),
                    subtitle: Text(
                      'Reminders for expiring items',
                      style: TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w500,
                          color: AppColors.textSecondary.withOpacity(0.8),
                          fontSize: 13),
                    ),
                    value: prefs.enabled,
                    activeColor: AppColors.primary,
                    onChanged: (val) {
                      ref
                          .read(notificationPreferencesProvider.notifier)
                          .toggleEnabled(val);
                    },
                  ),
                  const Divider(height: 1, color: AppColors.divider),
                  ListTile(
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.lg, vertical: AppSpacing.xs),
                    title: const Text(
                      'Remind days before expiry',
                      style: TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w700,
                          color: AppColors.textPrimary),
                    ),
                    trailing: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceVariant,
                        borderRadius:
                            BorderRadius.circular(AppSpacing.buttonRadius),
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<int>(
                          value: prefs.reminderDaysBefore,
                          icon: const Icon(Icons.keyboard_arrow_down_rounded,
                              color: AppColors.textSecondary),
                          style: const TextStyle(
                              fontFamily: 'Inter',
                              fontWeight: FontWeight.w800,
                              color: AppColors.textPrimary),
                          items: List.generate(8, (i) => i).map((days) {
                            return DropdownMenuItem(
                              value: days,
                              child: Text(days == 0
                                  ? 'Same day'
                                  : '$days day${days > 1 ? 's' : ''}'),
                            );
                          }).toList(growable: false),
                          onChanged: prefs.enabled
                              ? (val) {
                                  if (val != null) {
                                    ref
                                        .read(notificationPreferencesProvider
                                            .notifier)
                                        .setReminderDaysBefore(val);
                                  }
                                }
                              : null,
                        ),
                      ),
                    ),
                  ),
                  const Divider(height: 1, color: AppColors.divider),
                  ListTile(
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.lg, vertical: AppSpacing.sm),
                    title: const Text(
                      'Quiet hours',
                      style: TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w700,
                          color: AppColors.textPrimary),
                    ),
                    subtitle: Text(
                      'Do not disturb during these times',
                      style: TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w500,
                          color: AppColors.textSecondary.withOpacity(0.8),
                          fontSize: 13),
                    ),
                    trailing: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: prefs.enabled
                            ? AppColors.thisWeekSurface
                            : AppColors.surfaceVariant,
                        borderRadius:
                            BorderRadius.circular(AppSpacing.buttonRadius),
                        border: Border.all(
                            color: prefs.enabled
                                ? AppColors.thisWeek.withOpacity(0.3)
                                : Colors.transparent),
                      ),
                      child: Text(
                        prefs.quietHoursStart != null &&
                                prefs.quietHoursEnd != null
                            ? '${prefs.quietHoursStart!.format(context)} - ${prefs.quietHoursEnd!.format(context)}'
                            : 'Not set',
                        style: TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w800,
                          color: prefs.enabled
                              ? AppColors.thisWeek
                              : AppColors.textSecondary,
                        ),
                      ),
                    ),
                    enabled: prefs.enabled,
                    onTap: prefs.enabled
                        ? () async {
                            final start = await showTimePicker(
                              context: context,
                              initialTime: prefs.quietHoursStart ??
                                  const TimeOfDay(hour: 22, minute: 0),
                              helpText: 'Quiet hours start',
                            );
                            if (start == null || !context.mounted) return;
                            final end = await showTimePicker(
                              context: context,
                              initialTime: prefs.quietHoursEnd ??
                                  const TimeOfDay(hour: 8, minute: 0),
                              helpText: 'Quiet hours end',
                            );
                            if (end == null) return;
                            ref
                                .read(notificationPreferencesProvider.notifier)
                                .setQuietHours(start, end);
                          }
                        : null,
                  ),
                ],
              ),
              loading: () => const Padding(
                padding: EdgeInsets.all(AppSpacing.xl),
                child: Center(
                    child: CircularProgressIndicator(color: AppColors.primary)),
              ),
              error: (err, stack) => Padding(
                padding: const EdgeInsets.all(AppSpacing.lg),
                child: Text('Error loading preferences: $err',
                    style: const TextStyle(color: AppColors.error)),
              ),
            ),
          ),
          _buildSectionHeader('ACCOUNT'),
          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
              side: const BorderSide(color: AppColors.divider, width: 1),
            ),
            color: AppColors.surface,
            margin: const EdgeInsets.only(bottom: AppSpacing.xl),
            child: ListTile(
              contentPadding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.lg, vertical: AppSpacing.xs),
              title: const Text(
                'Household Management',
                style: TextStyle(
                    fontFamily: 'Inter',
                    fontWeight: FontWeight.w800,
                    color: AppColors.textPrimary),
              ),
              leading: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.primarySurface,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.home_rounded, color: AppColors.primary),
              ),
              trailing: const Icon(Icons.chevron_right_rounded,
                  color: AppColors.textSecondary),
              onTap: () {
                context.push('/household');
              },
            ),
          ),
          const SizedBox(height: AppSpacing.xxl),
          OutlinedButton.icon(
            onPressed: () async {
              final syncManager = ref.read(syncManagerProvider);
              final pending = await syncManager.pendingMutations();
              if (pending.isNotEmpty) {
                try {
                  await syncManager.flushPendingMutations();
                } catch (_) {
                  // flush threw — fall through to remaining check
                }
                final remaining = await syncManager.pendingMutations();
                if (remaining.isNotEmpty) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                          content:
                              Text('Sync pending changes before signing out')),
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
            icon: const Icon(Icons.logout_rounded),
            label: const Text('Sign Out'),
            style: OutlinedButton.styleFrom(
              foregroundColor: AppColors.error,
              side: const BorderSide(color: AppColors.error, width: 2),
              padding: const EdgeInsets.symmetric(vertical: 16),
              textStyle: const TextStyle(
                fontFamily: 'Inter',
                fontWeight: FontWeight.w800,
                fontSize: 16,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppSpacing.buttonRadius),
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.xl),
          Center(
            child: Text(
              'v1.0.0',
              style: TextStyle(
                fontFamily: 'Inter',
                fontWeight: FontWeight.w700,
                fontSize: 12,
                letterSpacing: 2,
                color: AppColors.textSecondary.withOpacity(0.5),
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.xxl),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding:
          const EdgeInsets.only(bottom: AppSpacing.sm, left: AppSpacing.sm),
      child: Text(
        title,
        style: const TextStyle(
          fontFamily: 'Inter',
          fontWeight: FontWeight.w900,
          fontSize: 13,
          letterSpacing: 1.5,
          color: AppColors.secondary,
        ),
      ),
    );
  }
}
