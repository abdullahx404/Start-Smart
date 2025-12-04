// Enhanced recommendation models for the LLM-powered recommendation engine
// Supports both fast (rule-only) and full (rule + LLM) modes

/// Category-specific score with reasoning
class CategoryScore {
  final double score;
  final String suitability;
  final String? reasoning;
  final List<String> positiveFactors;
  final List<String> concerns;
  final List<RuleTriggered>? rulesTriggered;

  CategoryScore({
    required this.score,
    required this.suitability,
    this.reasoning,
    this.positiveFactors = const [],
    this.concerns = const [],
    this.rulesTriggered,
  });

  /// Score as percentage (0-100)
  int get scorePercent => (score * 100).round();

  /// Check if this is a recommended location
  bool get isRecommended => score >= 0.45;

  /// Get color-coded suitability
  String get suitabilityEmoji {
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

  factory CategoryScore.fromJson(Map<String, dynamic> json) {
    return CategoryScore(
      score: (json['score'] as num).toDouble(),
      suitability: json['suitability'] as String? ?? 'moderate',
      reasoning: json['reasoning'] as String?,
      positiveFactors:
          (json['positive_factors'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      concerns:
          (json['concerns'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      rulesTriggered: (json['rules_triggered'] as List<dynamic>?)
          ?.map((e) => RuleTriggered.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'score': score,
    'suitability': suitability,
    'reasoning': reasoning,
    'positive_factors': positiveFactors,
    'concerns': concerns,
  };
}

/// Rule that was triggered during evaluation
class RuleTriggered {
  final String rule;
  final String delta;
  final String? reason;

  RuleTriggered({required this.rule, required this.delta, this.reason});

  bool get isPositive => delta.startsWith('+');

  factory RuleTriggered.fromJson(Map<String, dynamic> json) {
    return RuleTriggered(
      rule: json['rule'] as String,
      delta: json['delta'] as String,
      reason: json['reason'] as String?,
    );
  }
}

/// Overall recommendation summary
class RecommendationSummary {
  final String bestCategory;
  final double score;
  final String suitability;
  final String message;

  RecommendationSummary({
    required this.bestCategory,
    required this.score,
    required this.suitability,
    required this.message,
  });

  factory RecommendationSummary.fromJson(Map<String, dynamic> json) {
    return RecommendationSummary(
      bestCategory: json['best_category'] as String,
      score: (json['score'] as num).toDouble(),
      suitability: json['suitability'] as String,
      message: json['message'] as String,
    );
  }
}

/// LLM-specific insights
class LLMInsights {
  final List<String> keyFactors;
  final List<String> risks;
  final String recommendation;

  LLMInsights({
    required this.keyFactors,
    required this.risks,
    required this.recommendation,
  });

  factory LLMInsights.fromJson(Map<String, dynamic> json) {
    return LLMInsights(
      keyFactors:
          (json['key_factors'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      risks:
          (json['risks'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      recommendation: json['recommendation'] as String? ?? '',
    );
  }
}

/// Business Environment Vector summary (for debug/detail view)
class BEVSummary {
  final int restaurantCount;
  final int cafeCount;
  final int gymCount;
  final int officeCount;
  final int schoolCount;
  final double? distanceToMall;
  final String? incomeProxy;

  BEVSummary({
    this.restaurantCount = 0,
    this.cafeCount = 0,
    this.gymCount = 0,
    this.officeCount = 0,
    this.schoolCount = 0,
    this.distanceToMall,
    this.incomeProxy,
  });

  factory BEVSummary.fromJson(Map<String, dynamic> json) {
    return BEVSummary(
      restaurantCount: json['restaurant_count'] as int? ?? 0,
      cafeCount: json['cafe_count'] as int? ?? 0,
      gymCount: json['gym_count'] as int? ?? 0,
      officeCount: json['office_count'] as int? ?? 0,
      schoolCount: json['school_count'] as int? ?? 0,
      distanceToMall: (json['distance_to_mall'] as num?)?.toDouble(),
      incomeProxy: json['income_proxy'] as String?,
    );
  }
}

/// Enhanced recommendation response from the API
class EnhancedRecommendation {
  final String gridId;
  final String mode; // "fast" or "full"
  final double lat;
  final double lon;
  final int radius;
  final RecommendationSummary recommendation;
  final CategoryScore gym;
  final CategoryScore cafe;
  final LLMInsights? llmInsights;
  final BEVSummary? bev;
  final int processingTimeMs;

  EnhancedRecommendation({
    required this.gridId,
    required this.mode,
    required this.lat,
    required this.lon,
    required this.radius,
    required this.recommendation,
    required this.gym,
    required this.cafe,
    this.llmInsights,
    this.bev,
    required this.processingTimeMs,
  });

  /// Check if this is a full LLM-powered recommendation
  bool get isLLMPowered => mode == 'full' && llmInsights != null;

  /// Get the winning category
  String get winningCategory => recommendation.bestCategory;

  /// Get the winning score
  CategoryScore get winningScore =>
      recommendation.bestCategory == 'gym' ? gym : cafe;

  /// Compare gym vs cafe
  String get comparison {
    if (gym.score > cafe.score) {
      return 'Gym is ${((gym.score - cafe.score) * 100).round()}% better suited';
    } else if (cafe.score > gym.score) {
      return 'Cafe is ${((cafe.score - gym.score) * 100).round()}% better suited';
    }
    return 'Both categories equally suited';
  }

  factory EnhancedRecommendation.fromJson(Map<String, dynamic> json) {
    return EnhancedRecommendation(
      gridId: json['grid_id'] as String? ?? 'unknown',
      mode: json['mode'] as String? ?? 'fast',
      lat: (json['lat'] as num?)?.toDouble() ?? 0.0,
      lon: (json['lon'] as num?)?.toDouble() ?? 0.0,
      radius: json['radius'] as int? ?? 500,
      recommendation: RecommendationSummary.fromJson(
        json['recommendation'] as Map<String, dynamic>,
      ),
      gym: CategoryScore.fromJson(json['gym'] as Map<String, dynamic>),
      cafe: CategoryScore.fromJson(json['cafe'] as Map<String, dynamic>),
      llmInsights: json['llm_insights'] != null
          ? LLMInsights.fromJson(json['llm_insights'] as Map<String, dynamic>)
          : null,
      bev: json['bev'] != null
          ? BEVSummary.fromJson(json['bev'] as Map<String, dynamic>)
          : null,
      processingTimeMs: json['processing_time_ms'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
    'grid_id': gridId,
    'mode': mode,
    'lat': lat,
    'lon': lon,
    'radius': radius,
    'recommendation': {
      'best_category': recommendation.bestCategory,
      'score': recommendation.score,
      'suitability': recommendation.suitability,
      'message': recommendation.message,
    },
    'gym': gym.toJson(),
    'cafe': cafe.toJson(),
    'processing_time_ms': processingTimeMs,
  };
}

/// Request parameters for getting a recommendation
class RecommendationRequest {
  final double lat;
  final double lon;
  final int radius;

  RecommendationRequest({
    required this.lat,
    required this.lon,
    this.radius = 500,
  });

  Map<String, String> toQueryParams() => {
    'lat': lat.toString(),
    'lon': lon.toString(),
    'radius': radius.toString(),
  };
}
