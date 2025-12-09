/// Application-wide constants for StartSmart
library;

/// Environment configuration
/// Set to true for production deployment, false for local development
const bool kIsProduction = true; // Changed to true for Vercel deployment

/// API Configuration
class ApiConstants {
  // Local development URL
  static const String _localUrl = 'http://localhost:8000/api/v1';

  // Production URL (Vercel deployment)
  // UPDATE THIS after deploying backend to Vercel!
static const String _productionUrl =
    'https://startsmart-backend.vercel.app/api/v1';

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

  // Enhanced MVP Endpoints (LLM-powered)
  static const String recommendationFast = '/recommendation_fast';
  static const String recommendationLLM = '/recommendation_llm';
  static const String recommendationDebug = '/recommendation_debug';

  // Full URL helpers
  static String get neighborhoodsUrl => '$baseUrl$neighborhoods';
  static String get gridsUrl => '$baseUrl$grids';
  static String get recommendationsUrl => '$baseUrl$recommendations';
  static String gridDetailUrl(String gridId) => '$baseUrl$gridDetail/$gridId';
  static String get feedbackUrl => '$baseUrl$feedback';
  static String get healthUrl => '$baseUrl$health';

  // Enhanced MVP URL helpers
  static String get recommendationFastUrl => '$baseUrl$recommendationFast';
  static String get recommendationLLMUrl => '$baseUrl$recommendationLLM';
  static String get recommendationDebugUrl => '$baseUrl$recommendationDebug';

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

/// Enhanced MVP Suitability Thresholds
class SuitabilityThresholds {
  static const double excellent = 0.80;
  static const double good = 0.65;
  static const double moderate = 0.45;
  static const double poor = 0.25;
  // Below poor is "not_recommended"

  static String getSuitabilityLevel(double score) {
    if (score >= excellent) return 'excellent';
    if (score >= good) return 'good';
    if (score >= moderate) return 'moderate';
    if (score >= poor) return 'poor';
    return 'not_recommended';
  }

  static String getDisplayLabel(String suitability) {
    switch (suitability) {
      case 'excellent':
        return 'Excellent';
      case 'good':
        return 'Good';
      case 'moderate':
        return 'Moderate';
      case 'poor':
        return 'Poor';
      case 'not_recommended':
        return 'Not Recommended';
      default:
        return suitability;
    }
  }

  static String getEmoji(String suitability) {
    switch (suitability) {
      case 'excellent':
        return '🌟';
      case 'good':
        return '✅';
      case 'moderate':
        return '⚠️';
      case 'poor':
        return '❌';
      case 'not_recommended':
        return '🚫';
      default:
        return '❓';
    }
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
