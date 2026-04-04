import 'package:flutter/material.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';

class UrgencyBadge extends StatelessWidget {
  const UrgencyBadge({required this.bucket, super.key});

  final String bucket;

  @override
  Widget build(BuildContext context) {
    final (label, fg, bg) = _resolve(bucket);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: fg,
              fontWeight: FontWeight.w700,
            ),
      ),
    );
  }

  static (String, Color, Color) _resolve(String bucket) {
    return switch (bucket) {
      'expired' => ('Expired', AppColors.expired, AppColors.expiredSurface),
      'today' => ('Today', AppColors.today, AppColors.todaySurface),
      'this_week' => (
          'This Week',
          AppColors.thisWeek,
          AppColors.thisWeekSurface
        ),
      'safe_later' => ('Safe', AppColors.safeLater, AppColors.safeLaterSurface),
      _ => (bucket, AppColors.textSecondary, AppColors.surfaceVariant),
    };
  }
}
