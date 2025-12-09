/// Represents a location recommendation with explainability data
class Recommendation {
  final String gridId;
  final double gos;
  final double confidence;
  final String rationale;
  final double latCenter;
  final double lonCenter;
  final int businessCount;
  final int instagramVolume;
  final int redditMentions;
  final List<TopPost> topPosts;
  final List<Competitor> competitors;

  Recommendation({
    required this.gridId,
    required this.gos,
    required this.confidence,
    required this.rationale,
    required this.latCenter,
    required this.lonCenter,
    this.businessCount = 0,
    this.instagramVolume = 0,
    this.redditMentions = 0,
    this.topPosts = const [],
    this.competitors = const [],
  });

  /// Get total demand signals
  int get totalDemand => instagramVolume + redditMentions;

  /// Get opportunity level based on GOS
  String get opportunityLevel {
    if (gos >= 0.7) return 'High';
    if (gos >= 0.4) return 'Medium';
    return 'Low';
  }

  /// Get rank badge text (1st, 2nd, 3rd, etc.)
  String getRankBadge(int rank) {
    switch (rank) {
      case 1:
        return '🥇 #1';
      case 2:
        return '🥈 #2';
      case 3:
        return '🥉 #3';
      default:
        return '#$rank';
    }
  }

  /// Create from JSON (API response)
  factory Recommendation.fromJson(Map<String, dynamic> json) {
    return Recommendation(
      gridId: json['grid_id'] as String,
      gos: (json['gos'] as num).toDouble(),
      confidence: (json['confidence'] as num).toDouble(),
      rationale:
          json['rationale'] as String? ?? _generateDefaultRationale(json),
      latCenter: (json['lat_center'] as num).toDouble(),
      lonCenter: (json['lon_center'] as num).toDouble(),
      businessCount: json['business_count'] as int? ?? 0,
      instagramVolume: json['instagram_volume'] as int? ?? 0,
      redditMentions: json['reddit_mentions'] as int? ?? 0,
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
    );
  }

  /// Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'grid_id': gridId,
      'gos': gos,
      'confidence': confidence,
      'rationale': rationale,
      'lat_center': latCenter,
      'lon_center': lonCenter,
      'business_count': businessCount,
      'instagram_volume': instagramVolume,
      'reddit_mentions': redditMentions,
      'top_posts': topPosts.map((e) => e.toJson()).toList(),
      'competitors': competitors.map((e) => e.toJson()).toList(),
    };
  }

  /// Generate default rationale if not provided
  static String _generateDefaultRationale(Map<String, dynamic> json) {
    final businesses = json['business_count'] as int? ?? 0;
    final demand =
        (json['instagram_volume'] as int? ?? 0) +
        (json['reddit_mentions'] as int? ?? 0);
    return '$demand demand signals with $businesses competitors';
  }

  @override
  String toString() {
    return 'Recommendation($gridId, GOS: ${gos.toStringAsFixed(3)})';
  }
}

/// Represents a social media post used as evidence
class TopPost {
  final String source;
  final String text;
  final String timestamp;
  final String? link;

  TopPost({
    required this.source,
    required this.text,
    required this.timestamp,
    this.link,
  });

  /// Get source icon
  String get sourceIcon {
    switch (source.toLowerCase()) {
      case 'instagram':
        return '📷';
      case 'reddit':
        return '🤖';
      case 'simulated':
        return '🔬';
      default:
        return '📱';
    }
  }

  /// Get formatted timestamp
  String get formattedTimestamp {
    try {
      final date = DateTime.parse(timestamp);
      final now = DateTime.now();
      final diff = now.difference(date);

      if (diff.inDays > 30) {
        return '${diff.inDays ~/ 30} months ago';
      } else if (diff.inDays > 0) {
        return '${diff.inDays} days ago';
      } else if (diff.inHours > 0) {
        return '${diff.inHours} hours ago';
      } else {
        return 'Recently';
      }
    } catch (e) {
      return timestamp;
    }
  }

  factory TopPost.fromJson(Map<String, dynamic> json) {
    return TopPost(
      source: json['source'] as String? ?? 'unknown',
      text: json['text'] as String? ?? '',
      timestamp: json['timestamp'] as String? ?? '',
      link: json['link'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'source': source,
      'text': text,
      'timestamp': timestamp,
      'link': link,
    };
  }
}

/// Represents a competitor business
class Competitor {
  final String name;
  final double distanceKm;
  final double? rating;

  Competitor({required this.name, required this.distanceKm, this.rating});

  /// Get formatted distance
  String get formattedDistance {
    if (distanceKm < 1) {
      return '${(distanceKm * 1000).round()} m';
    }
    return '${distanceKm.toStringAsFixed(1)} km';
  }

  /// Get rating display
  String get ratingDisplay {
    if (rating == null) return 'No rating';
    return '⭐ ${rating!.toStringAsFixed(1)}';
  }

  factory Competitor.fromJson(Map<String, dynamic> json) {
    return Competitor(
      name: json['name'] as String? ?? 'Unknown',
      distanceKm: (json['distance_km'] as num?)?.toDouble() ?? 0.0,
      rating: (json['rating'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {'name': name, 'distance_km': distanceKm, 'rating': rating};
  }
}
