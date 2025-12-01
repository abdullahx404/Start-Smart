/// Application-wide constants for StartSmart
library;

/// Environment configuration
/// Set to true for production deployment, false for local development
const bool kIsProduction = false;

/// API Configuration
class ApiConstants {
  // Local development URL
  static const String _localUrl = 'http://localhost:8000/api/v1';

  // Production URL (Render deployment)
  // Update this with your actual Render URL after deployment
  static const String _productionUrl =
      'https://startsmart-api.onrender.com/api/v1';

  /// Get the active base URL based on environment
  static String get baseUrl => kIsProduction ? _productionUrl : _localUrl;

  // Legacy aliases for compatibility
  static const String productionUrl = _productionUrl;

  // Endpoints
  static const String neighborhoods = '/neighborhoods';
  static const String grids = '/grids';
  static const String recommendations = '/recommendations';
  static const String gridDetail = '/grid';
  static const String feedback = '/feedback';
  static const String health = '/health';

  // Full URL helpers
  static String get neighborhoodsUrl => '$baseUrl$neighborhoods';
  static String get gridsUrl => '$baseUrl$grids';
  static String get recommendationsUrl => '$baseUrl$recommendations';
  static String gridDetailUrl(String gridId) => '$baseUrl$gridDetail/$gridId';
  static String get feedbackUrl => '$baseUrl$feedback';
  static String get healthUrl => '$baseUrl$health';

  // Timeouts
  static const Duration connectionTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
}

/// Map Configuration
class MapConstants {
  // Karachi center coordinates
  static const double karachiLat = 24.8607;
  static const double karachiLon = 67.0011;

  // Default zoom levels
  static const double defaultZoom = 13.0;
  static const double minZoom = 10.0;
  static const double maxZoom = 18.0;
  static const double gridDetailZoom = 15.0;

  // Tile server
  static const String tileUrlTemplate =
      'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
  static const String tileUserAgent = 'StartSmart/1.0';
}

/// Business Categories
class Categories {
  static const String gym = 'Gym';
  static const String cafe = 'Cafe';

  static const List<String> all = [gym, cafe];

  static String getDisplayName(String category) {
    switch (category) {
      case gym:
        return 'Fitness / Gym';
      case cafe:
        return 'Cafe / Restaurant';
      default:
        return category;
    }
  }

  static String getIcon(String category) {
    switch (category) {
      case gym:
        return '🏋️';
      case cafe:
        return '☕';
      default:
        return '📍';
    }
  }
}

/// Supported Neighborhoods
class Neighborhoods {
  static const Map<String, String> all = {
    'DHA-Phase2': 'DHA Phase 2',
    'Clifton-Block2': 'Clifton Block 2',
    'Gulshan-e-Iqbal': 'Gulshan-e-Iqbal',
    'Saddar': 'Saddar',
    'PECHS': 'PECHS',
  };

  static String getDisplayName(String id) {
    return all[id] ?? id;
  }
}

/// GOS Score Thresholds
class GOSThresholds {
  static const double high = 0.7;
  static const double medium = 0.4;
  // Below medium is considered low

  static String getOpportunityLevel(double gos) {
    if (gos >= high) return 'High';
    if (gos >= medium) return 'Medium';
    return 'Low';
  }
}

/// UI Constants
class UIConstants {
  // Animation durations
  static const Duration shortAnimation = Duration(milliseconds: 200);
  static const Duration mediumAnimation = Duration(milliseconds: 350);
  static const Duration longAnimation = Duration(milliseconds: 500);

  // Padding
  static const double paddingSmall = 8.0;
  static const double paddingMedium = 16.0;
  static const double paddingLarge = 24.0;

  // Border radius
  static const double borderRadiusSmall = 8.0;
  static const double borderRadiusMedium = 12.0;
  static const double borderRadiusLarge = 16.0;

  // Card elevation
  static const double cardElevation = 2.0;
  static const double cardElevationHover = 4.0;
}
