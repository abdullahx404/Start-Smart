import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/grid.dart';
import '../models/recommendation.dart';
import '../models/grid_detail.dart';
import '../models/enhanced_recommendation.dart';
import '../utils/constants.dart';

/// Service for making API calls to the StartSmart backend
class ApiService {
  final String baseUrl;
  final http.Client _client;

  ApiService({String? baseUrl, http.Client? client})
    : baseUrl = baseUrl ?? ApiConstants.baseUrl,
      _client = client ?? http.Client();

  /// Get all available neighborhoods
  Future<List<Map<String, dynamic>>> getNeighborhoods() async {
    try {
      final response = await _client
          .get(Uri.parse('$baseUrl${ApiConstants.neighborhoods}'))
          .timeout(ApiConstants.connectionTimeout);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw ApiException(
          'Failed to fetch neighborhoods',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  /// Get all grids for a neighborhood and category
  Future<List<Grid>> getGrids({
    required String neighborhood,
    required String category,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl${ApiConstants.grids}').replace(
        queryParameters: {'neighborhood': neighborhood, 'category': category},
      );

      final response = await _client
          .get(uri)
          .timeout(ApiConstants.connectionTimeout);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => Grid.fromJson(json)).toList();
      } else {
        throw ApiException(
          'Failed to fetch grids',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  /// Get top recommendations for a neighborhood and category
  Future<List<Recommendation>> getRecommendations({
    required String neighborhood,
    required String category,
    int limit = 3,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl${ApiConstants.recommendations}').replace(
        queryParameters: {
          'neighborhood': neighborhood,
          'category': category,
          'limit': limit.toString(),
        },
      );

      final response = await _client
          .get(uri)
          .timeout(ApiConstants.connectionTimeout);

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        final List<dynamic> recommendations =
            data['recommendations'] ?? data['data'] ?? [];
        return recommendations
            .map((json) => Recommendation.fromJson(json))
            .toList();
      } else {
        throw ApiException(
          'Failed to fetch recommendations',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  /// Get detailed information for a specific grid
  Future<GridDetail> getGridDetail({
    required String gridId,
    required String category,
  }) async {
    try {
      final uri = Uri.parse(
        '$baseUrl${ApiConstants.gridDetail}/$gridId',
      ).replace(queryParameters: {'category': category});

      final response = await _client
          .get(uri)
          .timeout(ApiConstants.connectionTimeout);

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        return GridDetail.fromJson(data);
      } else {
        throw ApiException(
          'Failed to fetch grid detail',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  /// Submit user feedback for a grid
  Future<void> submitFeedback({
    required String gridId,
    required String category,
    required int rating, // -1 or 1
    String? comment,
  }) async {
    try {
      final response = await _client
          .post(
            Uri.parse('$baseUrl${ApiConstants.feedback}'),
            headers: {'Content-Type': 'application/json'},
            body: json.encode({
              'grid_id': gridId,
              'category': category,
              'rating': rating,
              'comment': comment,
            }),
          )
          .timeout(ApiConstants.connectionTimeout);

      if (response.statusCode != 201 && response.statusCode != 200) {
        throw ApiException(
          'Failed to submit feedback',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  // ============================================================
  // ENHANCED MVP ENDPOINTS (LLM-Powered Recommendations)
  // ============================================================

  /// Get fast recommendation (rule-based only, ~200ms)
  /// Use this for quick estimates without LLM processing
  Future<EnhancedRecommendation> getFastRecommendation({
    required double lat,
    required double lon,
    int radius = 500,
  }) async {
    try {
      final uri = Uri.parse(ApiConstants.recommendationFastUrl).replace(
        queryParameters: {
          'lat': lat.toString(),
          'lon': lon.toString(),
          'radius': radius.toString(),
        },
      );

      final response = await _client
          .get(uri)
          .timeout(ApiConstants.connectionTimeout);

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        return EnhancedRecommendation.fromJson(data);
      } else {
        throw ApiException(
          'Failed to fetch fast recommendation',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  /// Get LLM-powered recommendation (full analysis, ~2-3s)
  /// Use this for detailed AI-powered insights and reasoning
  Future<EnhancedRecommendation> getLLMRecommendation({
    required double lat,
    required double lon,
    int radius = 500,
  }) async {
    try {
      final uri = Uri.parse(ApiConstants.recommendationLLMUrl).replace(
        queryParameters: {
          'lat': lat.toString(),
          'lon': lon.toString(),
          'radius': radius.toString(),
        },
      );

      // LLM requests take longer, so extend timeout
      final response = await _client
          .get(uri)
          .timeout(const Duration(seconds: 60));

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        return EnhancedRecommendation.fromJson(data);
      } else {
        throw ApiException(
          'Failed to fetch LLM recommendation',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  /// Get debug recommendation with full pipeline details
  Future<Map<String, dynamic>> getDebugRecommendation({
    required double lat,
    required double lon,
    int radius = 500,
  }) async {
    try {
      final uri = Uri.parse(ApiConstants.recommendationDebugUrl).replace(
        queryParameters: {
          'lat': lat.toString(),
          'lon': lon.toString(),
          'radius': radius.toString(),
        },
      );

      final response = await _client
          .get(uri)
          .timeout(const Duration(seconds: 60));

      if (response.statusCode == 200) {
        return json.decode(response.body) as Map<String, dynamic>;
      } else {
        throw ApiException(
          'Failed to fetch debug recommendation',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  /// Dispose the HTTP client
  void dispose() {
    _client.close();
  }
}

/// Custom exception for API errors
class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, {this.statusCode});

  @override
  String toString() {
    if (statusCode != null) {
      return 'ApiException: $message (Status: $statusCode)';
    }
    return 'ApiException: $message';
  }
}
