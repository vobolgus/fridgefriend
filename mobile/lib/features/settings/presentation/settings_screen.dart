import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:package_info_plus/package_info_plus.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'package:fridgefriend_mobile/core/presentation/providers/theme_provider.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/app_bar.dart';
import 'providers.dart';

final _appVersionProvider = FutureProvider<String>((ref) async {
  final info = await PackageInfo.fromPlatform();
  return 'v${info.version} (${info.buildNumber})';
});

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final prefsAsync = ref.watch(notificationPreferencesProvider);
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      appBar: const FridgeFriendAppBar(title: 'Settings'),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: [
          _buildSectionHeader('PREFERENCES'),
          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
              side: BorderSide(color: theme.dividerColor, width: 1),
            ),
            color: theme.cardTheme.color,
            margin: const EdgeInsets.only(bottom: AppSpacing.xl),
            child: prefsAsync.when(
              data: (prefs) => Column(
                children: [
                  SwitchListTile(
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.lg, vertical: AppSpacing.sm),
                    title: Text(
                      'Push Notifications',
                      style: TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w800,
                          color: colorScheme.onSurface),
                    ),
                    subtitle: Text(
                      'Reminders for expiring items',
                      style: TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w500,
                          color: colorScheme.onSurfaceVariant,
                          fontSize: 13),
                    ),
                    value: prefs.enabled,
                    activeColor: AppColors.primary,
                    onChanged: (val) {
                      HapticFeedback.selectionClick();
                      ref
                          .read(notificationPreferencesProvider.notifier)
                          .toggleEnabled(val);
                    },
                  ),
                  Divider(height: 1, color: theme.dividerColor),
                  ListTile(
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.lg, vertical: AppSpacing.xs),
                    title: Text(
                      'Remind days before expiry',
                      style: TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w700,
                          color: colorScheme.onSurface),
                    ),
                    trailing: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      decoration: BoxDecoration(
                        color: theme.inputDecorationTheme.fillColor,
                        borderRadius:
                            BorderRadius.circular(AppSpacing.buttonRadius),
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<int>(
                          value: prefs.reminderDaysBefore,
                           icon: Icon(Icons.keyboard_arrow_down_rounded,
                              color: colorScheme.onSurfaceVariant),
                          style: TextStyle(
                              fontFamily: 'Inter',
                              fontWeight: FontWeight.w800,
                              color: colorScheme.onSurface),
                          dropdownColor: theme.cardTheme.color,
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
                  Divider(height: 1, color: theme.dividerColor),
                  ListTile(
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.lg, vertical: AppSpacing.sm),
                    title: Text(
                      'Quiet hours',
                      style: TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w700,
                          color: colorScheme.onSurface),
                    ),
                    subtitle: Text(
                      'Do not disturb during these times',
                      style: TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w500,
                          color: colorScheme.onSurfaceVariant,
                          fontSize: 13),
                    ),
                    trailing: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: prefs.enabled
                            ? AppColors.thisWeekSurface
                            : theme.inputDecorationTheme.fillColor,
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
                                : colorScheme.onSurfaceVariant,
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
          _buildSectionHeader('THEME'),
          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
              side: BorderSide(color: theme.dividerColor, width: 1),
            ),
            color: theme.cardTheme.color,
            margin: const EdgeInsets.only(bottom: AppSpacing.xl),
            child: Padding(
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.lg, vertical: AppSpacing.lg),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Appearance',
                    style: TextStyle(
                        fontFamily: 'Inter',
                        fontWeight: FontWeight.w800,
                        color: colorScheme.onSurface),
                  ),
                  const SizedBox(height: AppSpacing.md),
                  SegmentedButton<ThemeMode>(
                    segments: const [
                      ButtonSegment(
                        value: ThemeMode.system,
                        label: Text('System'),
                        icon: Icon(Icons.settings_system_daydream),
                      ),
                      ButtonSegment(
                        value: ThemeMode.light,
                        label: Text('Light'),
                        icon: Icon(Icons.light_mode),
                      ),
                      ButtonSegment(
                        value: ThemeMode.dark,
                        label: Text('Dark'),
                        icon: Icon(Icons.dark_mode),
                      ),
                    ],
                    selected: <ThemeMode>{ref.watch(themeModeProvider)},
                    onSelectionChanged: (Set<ThemeMode> newSelection) {
                      ref.read(themeModeProvider.notifier).state =
                          newSelection.first;
                    },
                    style: SegmentedButton.styleFrom(
                      backgroundColor: theme.colorScheme.surface,
                      selectedBackgroundColor: colorScheme.primaryContainer,
                      selectedForegroundColor: AppColors.primaryDark,
                      side: BorderSide(color: theme.dividerColor),
                      textStyle: const TextStyle(
                        fontFamily: 'Inter',
                        fontWeight: FontWeight.w700,
                        fontSize: 13,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          _buildSectionHeader('ACCOUNT'),
          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
              side: BorderSide(color: theme.dividerColor, width: 1),
            ),
            color: theme.cardTheme.color,
            margin: const EdgeInsets.only(bottom: AppSpacing.xl),
            child: ListTile(
              contentPadding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.lg, vertical: AppSpacing.xs),
              title: Text(
                'Household Management',
                style: TextStyle(
                    fontFamily: 'Inter',
                    fontWeight: FontWeight.w800,
                    color: colorScheme.onSurface),
              ),
              leading: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.home_rounded, color: AppColors.primary),
              ),
              trailing: Icon(Icons.chevron_right_rounded,
                  color: colorScheme.onSurfaceVariant),
              onTap: () {
                context.push('/household');
              },
            ),
          ),
          const SizedBox(height: AppSpacing.xxl),
          OutlinedButton.icon(
            onPressed: () async {
              final confirmed = await showDialog<bool>(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('Sign Out',
                      style: TextStyle(
                          fontFamily: 'Inter', fontWeight: FontWeight.w800)),
                  content: const Text('Are you sure you want to sign out?'),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(context, false),
                        child: const Text('Cancel')),
                    FilledButton(
                      onPressed: () => Navigator.pop(context, true),
                      style: FilledButton.styleFrom(
                          backgroundColor: AppColors.error),
                      child: const Text('Sign Out'),
                    ),
                  ],
                ),
              );
              if (confirmed == true) {
                HapticFeedback.heavyImpact();
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
                            content: Text(
                                'Sync pending changes before signing out')),
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
              }
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
            child: ref.watch(_appVersionProvider).when(
                  data: (version) => Text(
                    version,
                    style: TextStyle(
                      fontFamily: 'Inter',
                      fontWeight: FontWeight.w700,
                      fontSize: 12,
                      letterSpacing: 2,
                      color: colorScheme.onSurfaceVariant.withValues(alpha: 0.5),
                    ),
                  ),
                  loading: () => const SizedBox.shrink(),
                  error: (_, __) => Text(
                    'v0.1.0',
                    style: TextStyle(
                      fontFamily: 'Inter',
                      fontWeight: FontWeight.w700,
                      fontSize: 12,
                      letterSpacing: 2,
                      color: colorScheme.onSurfaceVariant.withValues(alpha: 0.5),
                    ),
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
