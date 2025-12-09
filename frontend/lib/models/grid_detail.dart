import 'recommendation.dart';

/// Detailed grid information including explainability data
class GridDetail {
  final String gridId;
  final String neighborhood;
  final double latCenter;
  final double lonCenter;
  final double latNorth;
  final double latSouth;
  final double lonEast;
  final double lonWest;
  final double gos;
  final double confidence;
  final GridMetrics metrics;
  final List<TopPost> topPosts;
  final List<Competitor> competitors;
  final String? rationale;

  GridDetail({
    required this.gridId,
    required this.neighborhood,
    required this.latCenter,
    required this.lonCenter,
    required this.latNorth,
    required this.latSouth,
    required this.lonEast,
    required this.lonWest,
    required this.gos,
    required this.confidence,
    required this.metrics,
    this.topPosts = const [],
    this.competitors = const [],
    this.rationale,
  });

  /// Get opportunity level based on GOS
  String get opportunityLevel {
    if (gos >= 0.7) return 'High Opportunity';
    if (gos >= 0.4) return 'Medium Opportunity';
    return 'Low Opportunity';
  }

  /// Get confidence level description
  String get confidenceLevel {
    if (confidence >= 0.7) return 'High Confidence';
    if (confidence >= 0.4) return 'Medium Confidence';
    return 'Low Confidence';
  }

  /// Create from JSON (API response)
  factory GridDetail.fromJson(Map<String, dynamic> json) {
    // Handle nested metrics or flat structure
    final metricsJson = json['metrics'] as Map<String, dynamic>? ?? json;

    return GridDetail(
      gridId: json['grid_id'] as String,
      neighborhood:
          json['neighborhood'] as String? ??
          _extractNeighborhood(json['grid_id'] as String),
      latCenter: (json['lat_center'] as num).toDouble(),
      lonCenter: (json['lon_center'] as num).toDouble(),
      latNorth:
          (json['lat_north'] as num?)?.toDouble() ??
          (json['lat_center'] as num).toDouble() + 0.0045,
      latSouth:
          (json['lat_south'] as num?)?.toDouble() ??
          (json['lat_center'] as num).toDouble() - 0.0045,
      lonEast:
          (json['lon_east'] as num?)?.toDouble() ??
          (json['lon_center'] as num).toDouble() + 0.005,
      lonWest:
          (json['lon_west'] as num?)?.toDouble() ??
          (json['lon_center'] as num).toDouble() - 0.005,
      gos: (json['gos'] as num).toDouble(),
      confidence: (json['confidence'] as num).toDouble(),
      metrics: GridMetrics.fromJson(metricsJson),
      topPosts:
          (json['top_posts'] as List<dynamic>?)
              ?.map((e) => TopPost.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      competitors:
          (json['competitors'] as List<dynamic>?)
              ?.map((e) => Competitor.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      rationale: json['rationale'] as String?,
    );
  }

  /// Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'grid_id': gridId,
      'neighborhood': neighborhood,
      'lat_center': latCenter,
      'lon_center': lonCenter,
      'lat_north': latNorth,
      'lat_south': latSouth,
      'lon_east': lonEast,
      'lon_west': lonWest,
      'gos': gos,
      'confidence': confidence,
      'metrics': metrics.toJson(),
      'top_posts': topPosts.map((e) => e.toJson()).toList(),
      'competitors': competitors.map((e) => e.toJson()).toList(),
      'rationale': rationale,
    };
  }

  /// Extract neighborhood from grid_id
  static String _extractNeighborhood(String gridId) {
    final parts = gridId.split('-Cell-');
    if (parts.isNotEmpty) {
      return parts[0].replaceAll('-', ' ');
    }
    return gridId;
  }

  @override
  String toString() {
    return 'GridDetail($gridId, GOS: ${gos.toStringAsFixed(3)})';
  }
}

/// Grid metrics breakdown
class GridMetrics {
  final int businessCount;
  final int instagramVolume;
  final int redditMentions;
  final double? avgRating;
  final int? totalReviews;

  GridMetrics({
    required this.businessCount,
    required this.instagramVolume,
    required this.redditMentions,
    this.avgRating,
    this.totalReviews,
  });

  /// Get total demand signals
  int get totalDemand => instagramVolume + redditMentions;

  /// Get competition level description
  String get competitionLevel {
    if (businessCount == 0) return 'No Competition';
    if (businessCount <= 2) return 'Low Competition';
    if (businessCount <= 5) return 'Medium Competition';
    return 'High Competition';
  }

  /// Get demand level description
  String get demandLevel {
    if (totalDemand <= 20) return 'Low Demand';
    if (totalDemand <= 50) return 'Medium Demand';
    return 'High Demand';
  }

  factory GridMetrics.fromJson(Map<String, dynamic> json) {
    return GridMetrics(
      businessCount: json['business_count'] as int? ?? 0,
      instagramVolume: json['instagram_volume'] as int? ?? 0,
      redditMentions: json['reddit_mentions'] as int? ?? 0,
      avgRating: (json['avg_rating'] as num?)?.toDouble(),
      totalReviews: json['total_reviews'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'business_count': businessCount,
      'instagram_volume': instagramVolume,
      'reddit_mentions': redditMentions,
      'avg_rating': avgRating,
      'total_reviews': totalReviews,
    };
  }
}
