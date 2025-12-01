import 'package:flutter/material.dart';

/// Application color palette for StartSmart
class AppColors {
  // Primary brand colors
  static const Color primary = Color(0xFF2E7D32); // Forest green
  static const Color primaryLight = Color(0xFF60AD5E);
  static const Color primaryDark = Color(0xFF005005);

  // Secondary accent
  static const Color secondary = Color(0xFF1976D2); // Blue
  static const Color secondaryLight = Color(0xFF63A4FF);
  static const Color secondaryDark = Color(0xFF004BA0);

  // Background colors
  static const Color background = Color(0xFFF5F5F5);
  static const Color surface = Colors.white;
  static const Color surfaceVariant = Color(0xFFE8E8E8);

  // Text colors
  static const Color textPrimary = Color(0xFF212121);
  static const Color textSecondary = Color(0xFF757575);
  static const Color textHint = Color(0xFF9E9E9E);
  static const Color textOnPrimary = Colors.white;

  // GOS Heatmap colors (low to high opportunity)
  static const Color gosVeryLow = Color(0xFFE53935); // Red
  static const Color gosLow = Color(0xFFFF7043); // Deep orange
  static const Color gosMedium = Color(0xFFFFCA28); // Amber
  static const Color gosHigh = Color(0xFF66BB6A); // Light green
  static const Color gosVeryHigh = Color(0xFF2E7D32); // Dark green

  // Status colors
  static const Color success = Color(0xFF4CAF50);
  static const Color warning = Color(0xFFFFC107);
  static const Color error = Color(0xFFF44336);
  static const Color info = Color(0xFF2196F3);

  // Confidence indicator colors
  static const Color confidenceHigh = Color(0xFF4CAF50);
  static const Color confidenceMedium = Color(0xFFFFC107);
  static const Color confidenceLow = Color(0xFFFF9800);

  // Map overlay
  static const Color mapOverlay = Color(0x40000000);
  static const Color gridBorder = Color(0xFF424242);
  static const Color gridBorderSelected = Color(0xFF1976D2);

  /// Get GOS color based on score (0.0 - 1.0)
  static Color getGOSColor(double gos) {
    if (gos >= 0.8) return gosVeryHigh;
    if (gos >= 0.6) return gosHigh;
    if (gos >= 0.4) return gosMedium;
    if (gos >= 0.2) return gosLow;
    return gosVeryLow;
  }

  /// Get GOS color with opacity for heatmap overlay
  static Color getGOSColorWithOpacity(double gos, {double opacity = 0.5}) {
    return getGOSColor(gos).withValues(alpha: opacity);
  }

  /// Get confidence color based on score (0.0 - 1.0)
  static Color getConfidenceColor(double confidence) {
    if (confidence >= 0.7) return confidenceHigh;
    if (confidence >= 0.4) return confidenceMedium;
    return confidenceLow;
  }

  /// Generate gradient for GOS scale legend
  static List<Color> get gosGradient => [
    gosVeryLow,
    gosLow,
    gosMedium,
    gosHigh,
    gosVeryHigh,
  ];
}

/// Theme data for the app
class AppTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.primary,
        brightness: Brightness.light,
      ),
      scaffoldBackgroundColor: AppColors.background,
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.primary,
        foregroundColor: AppColors.textOnPrimary,
        elevation: 0,
      ),
      cardTheme: CardThemeData(
        color: AppColors.surface,
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: AppColors.textOnPrimary,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.surface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.surfaceVariant),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.surfaceVariant),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.primary, width: 2),
        ),
      ),
      textTheme: const TextTheme(
        headlineLarge: TextStyle(
          color: AppColors.textPrimary,
          fontWeight: FontWeight.bold,
        ),
        headlineMedium: TextStyle(
          color: AppColors.textPrimary,
          fontWeight: FontWeight.w600,
        ),
        bodyLarge: TextStyle(color: AppColors.textPrimary),
        bodyMedium: TextStyle(color: AppColors.textSecondary),
      ),
    );
  }
}
