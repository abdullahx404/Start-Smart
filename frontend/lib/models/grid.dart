import 'package:latlong2/latlong.dart';

/// Represents a grid cell with GOS score and metadata
class Grid {
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
  final int businessCount;
  final int instagramVolume;
  final int redditMentions;

  Grid({
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
    this.businessCount = 0,
    this.instagramVolume = 0,
    this.redditMentions = 0,
  });

  /// Get center point as LatLng
  LatLng get center => LatLng(latCenter, lonCenter);

  /// Get bounding box corners
  List<LatLng> get boundingBox => [
    LatLng(latNorth, lonWest), // NW
    LatLng(latNorth, lonEast), // NE
    LatLng(latSouth, lonEast), // SE
    LatLng(latSouth, lonWest), // SW
  ];

  /// Get total demand signals
  int get totalDemand => instagramVolume + redditMentions;

  /// Get opportunity level based on GOS
  String get opportunityLevel {
    if (gos >= 0.7) return 'High';
    if (gos >= 0.4) return 'Medium';
    return 'Low';
  }

  /// Create from JSON (API response)
  factory Grid.fromJson(Map<String, dynamic> json) {
    return Grid(
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
      businessCount: json['business_count'] as int? ?? 0,
      instagramVolume: json['instagram_volume'] as int? ?? 0,
      redditMentions: json['reddit_mentions'] as int? ?? 0,
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
      'business_count': businessCount,
      'instagram_volume': instagramVolume,
      'reddit_mentions': redditMentions,
    };
  }

  /// Extract neighborhood from grid_id (e.g., "DHA-Phase2-Cell-01" -> "DHA Phase 2")
  static String _extractNeighborhood(String gridId) {
    final parts = gridId.split('-Cell-');
    if (parts.isNotEmpty) {
      return parts[0].replaceAll('-', ' ');
    }
    return gridId;
  }

  @override
  String toString() {
    return 'Grid($gridId, GOS: ${gos.toStringAsFixed(3)}, Confidence: ${confidence.toStringAsFixed(3)})';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is Grid && other.gridId == gridId;
  }

  @override
  int get hashCode => gridId.hashCode;
}
