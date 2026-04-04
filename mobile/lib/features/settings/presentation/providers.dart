import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/settings/data/push_notification_service.dart';

class NotificationPreferences {
  const NotificationPreferences({
    required this.enabled,
    required this.reminderDaysBefore,
    this.quietHoursStart,
    this.quietHoursEnd,
  });

  final bool enabled;
  final int reminderDaysBefore;
  final TimeOfDay? quietHoursStart;
  final TimeOfDay? quietHoursEnd;
}

TimeOfDay? _parseTime(dynamic value) {
  if (value == null) return null;
  final str = value.toString();
  final parts = str.split(':');
  if (parts.length >= 2) {
    final hour = int.tryParse(parts[0]) ?? 0;
    final minute = int.tryParse(parts[1]) ?? 0;
    return TimeOfDay(hour: hour, minute: minute);
  }
  return null;
}

String _formatTime(TimeOfDay time) {
  return '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}:00';
}

class NotificationPreferencesNotifier extends AsyncNotifier<NotificationPreferences> {
  @override
  Future<NotificationPreferences> build() async {
    final apiClient = ref.watch(apiClientProvider);
    final prefs = await apiClient.getNotificationPreferences();
    return NotificationPreferences(
      enabled: prefs['expiry_reminder_enabled'] as bool? ?? false,
      reminderDaysBefore: prefs['reminder_days_before'] as int? ?? 1,
      quietHoursStart: _parseTime(prefs['quiet_hours_start']),
      quietHoursEnd: _parseTime(prefs['quiet_hours_end']),
    );
  }

  Future<void> toggleEnabled(bool enabled) async {
    final current = state.valueOrNull;
    if (current == null) return;
    try {
      final apiClient = ref.read(apiClientProvider);
      await apiClient.updateNotificationPreferences(expiryReminderEnabled: enabled);
      state = AsyncValue.data(NotificationPreferences(
        enabled: enabled,
        reminderDaysBefore: current.reminderDaysBefore,
        quietHoursStart: current.quietHoursStart,
        quietHoursEnd: current.quietHoursEnd,
      ));
    } catch (_) {
      state = AsyncValue.data(current);
    }
  }

  Future<void> setReminderDaysBefore(int days) async {
    final current = state.valueOrNull;
    if (current == null) return;
    try {
      final apiClient = ref.read(apiClientProvider);
      await apiClient.updateNotificationPreferences(reminderDaysBefore: days);
      state = AsyncValue.data(NotificationPreferences(
        enabled: current.enabled,
        reminderDaysBefore: days,
        quietHoursStart: current.quietHoursStart,
        quietHoursEnd: current.quietHoursEnd,
      ));
    } catch (_) {
      state = AsyncValue.data(current);
    }
  }

  Future<void> setQuietHours(TimeOfDay? start, TimeOfDay? end) async {
    final current = state.valueOrNull;
    if (current == null) return;
    try {
      final apiClient = ref.read(apiClientProvider);
      await apiClient.updateNotificationPreferences(
        quietHoursStart: start != null ? _formatTime(start) : null,
        quietHoursEnd: end != null ? _formatTime(end) : null,
      );
      state = AsyncValue.data(NotificationPreferences(
        enabled: current.enabled,
        reminderDaysBefore: current.reminderDaysBefore,
        quietHoursStart: start,
        quietHoursEnd: end,
      ));
    } catch (_) {
      state = AsyncValue.data(current);
    }
  }
}

final notificationPreferencesProvider =
    AsyncNotifierProvider<NotificationPreferencesNotifier, NotificationPreferences>(
      NotificationPreferencesNotifier.new,
    );

class NotificationsNotifier extends AsyncNotifier<bool> {
  @override
  Future<bool> build() async {
    final apiClient = ref.watch(apiClientProvider);
    final prefs = await apiClient.getNotificationPreferences();
    return prefs['expiry_reminder_enabled'] as bool? ?? false;
  }

  Future<void> toggle(bool enabled) async {
    final current = state.valueOrNull;
    try {
      final apiClient = ref.read(apiClientProvider);
      await apiClient.updateNotificationPreferences(expiryReminderEnabled: enabled);
      state = AsyncValue.data(enabled);
    } catch (_) {
      if (current != null) {
        state = AsyncValue.data(current);
      }
    }
  }
}

final notificationsEnabledProvider =
    AsyncNotifierProvider<NotificationsNotifier, bool>(NotificationsNotifier.new);

final pushNotificationServiceProvider = Provider<PushNotificationService>((ref) {
  if (useMockAuth) {
    return MockPushNotificationService();
  }
  return FirebasePushNotificationService();
});

/// Registers the device token with the backend on first access.
/// Watch this provider after sign-in to trigger automatic registration.
final deviceTokenRegistrationProvider = FutureProvider<void>((ref) async {
  final pushService = ref.watch(pushNotificationServiceProvider);
  final apiClient = ref.watch(apiClientProvider);
  await pushService.registerToken(apiClient);
});
