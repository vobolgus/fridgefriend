import 'package:flutter/material.dart';

abstract final class AppSpacing {
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 24;
  static const double xxl = 32;
  static const double xxxl = 48;

  static const screenPadding =
      EdgeInsets.symmetric(horizontal: lg, vertical: md);
  static const cardPadding = EdgeInsets.all(lg);
  static const listItemPadding =
      EdgeInsets.symmetric(horizontal: lg, vertical: md);

  static const cardRadius = 16.0;
  static const chipRadius = 20.0;
  static const buttonRadius = 12.0;
  static const inputRadius = 12.0;
  static const bottomSheetRadius = 24.0;
}
