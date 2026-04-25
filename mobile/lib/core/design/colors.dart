import 'package:flutter/material.dart';

abstract final class AppColors {
  static const primary = Color(0xFF00C853);
  static const primaryDark = Color(0xFF009624);
  static const primaryLight = Color(0xFFB9F6CA);
  static const primarySurface = Color(0xFFE8F5E9);

  static const secondary = Color(0xFF651FFF);
  static const secondaryLight = Color(0xFFEDE7F6);

  static const accent = Color(0xFFFF6D00);
  static const accentLight = Color(0xFFFFF3E0);

  static const error = Color(0xFFD50000);
  static const errorLight = Color(0xFFFFEBEE);

  static const expired = Color(0xFFD50000);
  static const expiredSurface = Color(0xFFFFCDD2);
  static const today = Color(0xFFFF6D00);
  static const todaySurface = Color(0xFFFFE0B2);
  static const thisWeek = Color(0xFFFFAB00);
  static const thisWeekSurface = Color(0xFFFFF8E1);
  static const safeLater = Color(0xFF00C853);
  static const safeLaterSurface = Color(0xFFC8E6C9);

  static const textPrimary = Color(0xFF1A1A2E);
  static const textPrimaryDark = Color(0xFFF0F0F5);
  static const textSecondary = Color(0xFF6B7280);
  static const textSecondaryDark = Color(0xFF9CA3AF);
  static const textOnPrimary = Colors.white;
  static const textOnDark = Colors.white;

  static const surface = Colors.white;
  static const surfaceDark = Color(0xFF1A1A2E);
  static const surfaceVariant = Color(0xFFF5F5F7);
  static const surfaceVariantDark = Color(0xFF252540);
  static const background = Color(0xFFFAFAFC);
  static const backgroundDark = Color(0xFF121220);
  static const divider = Color(0xFFE5E7EB);
  static const dividerDark = Color(0xFF2D2D4A);

  static const navBarBackground = Colors.white;
  static const navBarBackgroundDark = Color(0xFF1A1A2E);
  static const shimmerBase = Color(0xFFE0E0E0);
  static const shimmerHighlight = Color(0xFFF5F5F5);

  // === M3 Dark Surface Container Hierarchy ===
  // Generated from a tonal palette anchored on backgroundDark (#121220).
  // Each step ~+4-6 luminance for visible elevation tiers in dark mode.
  static const surfaceContainerLowestDark = Color(0xFF0E0E1A);
  static const surfaceContainerLowDark = Color(0xFF161624);
  static const surfaceContainerDark = Color(0xFF1C1C2E);
  static const surfaceContainerHighDark = Color(0xFF222236);
  static const surfaceContainerHighestDark = Color(0xFF2A2A40);

  // === Brand color refinements for dark ===
  // Lifted dark primary for better contrast on dark surfaces (per design decision).
  static const primaryLifted = Color(0xFF5BD178); // dark-mode primary override
  // onPrimaryDark is what should be used as foreground on primaryLifted.
  // 90% opaque near-black for strong contrast against the lifted green.
  static const onPrimaryDark = Color(0xFF00390C);

  // === Muted dark status colors (M3 spec) ===
  // Replaces saturated Colors.red etc. which are eyestrain in dark.
  static const errorDark = Color(0xFFFFB4AB); // M3 dark error baseline
  static const errorContainerDark = Color(0xFF93000A);
  static const onErrorDark = Color(0xFF690005);
  static const onErrorContainerDark = Color(0xFFFFDAD6);

  // === Urgency dark variants ===
  // Same hue family as light, lifted for legibility on dark surfaces.
  static const expiredDark = Color(0xFFFFB4AB); // pinkish red
  static const expiredSurfaceDark = Color(0xFF410002);
  static const todayDark = Color(0xFFFFB59E); // warm coral
  static const todaySurfaceDark = Color(0xFF5C1900);
  static const thisWeekDark = Color(0xFFFFD37D); // muted amber
  static const thisWeekSurfaceDark = Color(0xFF402D00);
  static const safeLaterDark = Color(0xFF7CDC97); // soft green
  static const safeLaterSurfaceDark = Color(0xFF003919);

  // === Shimmer (loading) dark variants ===
  static const shimmerBaseDark = Color(0xFF222236);
  static const shimmerHighlightDark = Color(0xFF2D2D45);

  // === Scrim (image/camera overlays) ===
  static const scrim = Color(0xFF000000); // M3 scrim is always pure black
}
