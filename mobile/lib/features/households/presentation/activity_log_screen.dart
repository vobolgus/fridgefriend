import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/empty_state.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/error_view.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/loading_view.dart';
import 'package:fridgefriend_mobile/features/households/presentation/providers.dart';

class ActivityLogScreen extends ConsumerWidget {
  final String householdId;

  const ActivityLogScreen({super.key, required this.householdId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final activityAsync = ref.watch(activityLogProvider(householdId));

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text(
          'Activity Log',
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
      body: activityAsync.when(
        data: (events) {
          if (events.isEmpty) {
            return const EmptyState(
              icon: Icons.history_rounded,
              title: 'No activity yet',
              subtitle:
                  'Things are quiet right now. Add some items to get started!',
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.lg, vertical: AppSpacing.xl),
            itemCount: events.length,
            itemBuilder: (context, index) {
              final event = events[index];
              final action =
                  (event['action'] as String? ?? 'Unknown').toLowerCase();
              final userId = event['user_id'] as String? ?? 'Unknown User';
              final timestampStr = event['created_at'] as String?;
              final timestamp =
                  timestampStr != null ? DateTime.tryParse(timestampStr) : null;

              final newState = event['new_state'] as Map<String, dynamic>?;
              final previousState =
                  event['previous_state'] as Map<String, dynamic>?;
              final itemName =
                  (newState?['displayName'] ?? newState?['display_name']) ??
                      (previousState?['displayName'] ??
                          previousState?['display_name']) ??
                      'Unknown Item';

              Color badgeColor;
              Color badgeSurface;
              String actionText;

              if (action.contains('create') || action.contains('add')) {
                badgeColor = AppColors.primary;
                badgeSurface = AppColors.primarySurface;
                actionText = 'ADDED';
              } else if (action.contains('update') || action.contains('edit')) {
                badgeColor = AppColors.thisWeek;
                badgeSurface = AppColors.thisWeekSurface;
                actionText = 'UPDATED';
              } else if (action.contains('delete') ||
                  action.contains('discard') ||
                  action.contains('remove')) {
                badgeColor = AppColors.error;
                badgeSurface = AppColors.errorLight;
                actionText = 'REMOVED';
              } else if (action.contains('consume') || action.contains('use')) {
                badgeColor = AppColors.accent;
                badgeSurface = AppColors.accentLight;
                actionText = 'USED';
              } else {
                badgeColor = AppColors.textSecondary;
                badgeSurface = AppColors.surfaceVariant;
                actionText = action.toUpperCase();
              }

              final isLast = index == events.length - 1;

              return IntrinsicHeight(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    SizedBox(
                      width: 32,
                      child: Stack(
                        alignment: Alignment.topCenter,
                        children: [
                          if (!isLast)
                            Positioned(
                              top: 16,
                              bottom: 0,
                              child: Container(
                                width: 2,
                                color: AppColors.divider,
                              ),
                            ),
                          Container(
                            margin: const EdgeInsets.only(top: 8),
                            width: 16,
                            height: 16,
                            decoration: BoxDecoration(
                              color: badgeColor,
                              shape: BoxShape.circle,
                              border: Border.all(
                                color: AppColors.background,
                                width: 3,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(
                      child: Container(
                        margin: const EdgeInsets.only(bottom: AppSpacing.lg),
                        decoration: BoxDecoration(
                          color: AppColors.surface,
                          borderRadius:
                              BorderRadius.circular(AppSpacing.cardRadius),
                          border:
                              Border.all(color: AppColors.divider, width: 1),
                          boxShadow: [
                            BoxShadow(
                              color: AppColors.textPrimary.withOpacity(0.03),
                              blurRadius: 8,
                              offset: const Offset(0, 2),
                            ),
                          ],
                        ),
                        padding: const EdgeInsets.all(AppSpacing.lg),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  userId,
                                  style: const TextStyle(
                                    fontFamily: 'Inter',
                                    fontWeight: FontWeight.w800,
                                    fontSize: 16,
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: badgeSurface,
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text(
                                    actionText,
                                    style: TextStyle(
                                      fontFamily: 'Inter',
                                      fontWeight: FontWeight.w900,
                                      fontSize: 10,
                                      color: badgeColor,
                                      letterSpacing: 0.5,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: AppSpacing.sm),
                            Text(
                              itemName,
                              style: const TextStyle(
                                fontFamily: 'Inter',
                                fontWeight: FontWeight.w600,
                                fontSize: 18,
                                color: AppColors.textPrimary,
                              ),
                            ),
                            const SizedBox(height: AppSpacing.xs),
                            if (timestamp != null)
                              Text(
                                '${_getMonth(timestamp.month)} ${timestamp.day}, ${timestamp.year} • ${_formatTime(timestamp.toLocal())}',
                                style: TextStyle(
                                  fontFamily: 'Inter',
                                  fontWeight: FontWeight.w600,
                                  fontSize: 12,
                                  color:
                                      AppColors.textSecondary.withOpacity(0.7),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          );
        },
        loading: () => const LoadingView(message: 'Loading activity...'),
        error: (err, _) => ErrorView(message: 'Error loading activity: $err'),
      ),
    );
  }

  String _getMonth(int month) {
    const months = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec'
    ];
    if (month >= 1 && month <= 12) {
      return months[month - 1];
    }
    return '';
  }

  String _formatTime(DateTime time) {
    final hour =
        time.hour == 0 ? 12 : (time.hour > 12 ? time.hour - 12 : time.hour);
    final minute = time.minute.toString().padLeft(2, '0');
    final period = time.hour >= 12 ? 'PM' : 'AM';
    return '$hour:$minute $period';
  }
}
