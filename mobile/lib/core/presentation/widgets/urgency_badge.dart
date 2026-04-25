import 'package:flutter/material.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';

class UrgencyBadge extends StatefulWidget {
  const UrgencyBadge({required this.bucket, super.key});

  final String bucket;

  @override
  State<UrgencyBadge> createState() => _UrgencyBadgeState();
}

class _UrgencyBadgeState extends State<UrgencyBadge>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1),
    );
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.05).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );

    if (widget.bucket == 'expired' || widget.bucket == 'today') {
      _controller.repeat(reverse: true);
    }
  }

  @override
  void didUpdateWidget(UrgencyBadge oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.bucket != oldWidget.bucket) {
      if (widget.bucket == 'expired' || widget.bucket == 'today') {
        _controller.repeat(reverse: true);
      } else {
        _controller.stop();
        _controller.value = 0.0;
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final (label, fg, bg) =
        _resolve(widget.bucket, Theme.of(context).brightness);

    final badge = Container(
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

    if (widget.bucket == 'expired' || widget.bucket == 'today') {
      return ScaleTransition(
        scale: _pulseAnimation,
        child: badge,
      );
    }

    return badge;
  }

  static (String, Color, Color) _resolve(String bucket, Brightness brightness) {
    final isDark = brightness == Brightness.dark;
    return switch (bucket) {
      'expired' => (
          'Expired',
          isDark ? AppColors.expiredDark : AppColors.expired,
          isDark ? AppColors.expiredSurfaceDark : AppColors.expiredSurface,
        ),
      'today' => (
          'Today',
          isDark ? AppColors.todayDark : AppColors.today,
          isDark ? AppColors.todaySurfaceDark : AppColors.todaySurface,
        ),
      'this_week' => (
          'This Week',
          isDark ? AppColors.thisWeekDark : AppColors.thisWeek,
          isDark ? AppColors.thisWeekSurfaceDark : AppColors.thisWeekSurface,
        ),
      'safe_later' => (
          'Safe',
          isDark ? AppColors.safeLaterDark : AppColors.safeLater,
          isDark ? AppColors.safeLaterSurfaceDark : AppColors.safeLaterSurface,
        ),
      _ => (
          bucket,
          isDark ? AppColors.textSecondaryDark : AppColors.textSecondary,
          isDark ? AppColors.surfaceVariantDark : AppColors.surfaceVariant,
        ),
    };
  }
}
