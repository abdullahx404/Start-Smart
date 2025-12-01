import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/grid.dart';
import '../models/recommendation.dart';
import '../models/grid_detail.dart';
import '../services/api_service.dart';
import '../services/mock_data_service.dart';
import 'selection_provider.dart';

/// Provider for API service instance
final apiServiceProvider = Provider<ApiService>((ref) {
  return ApiService();
});

/// Provider for mock data service
final mockDataServiceProvider = Provider<MockDataService>((ref) {
  return MockDataService();
});

/// Whether to use mock data (for offline/demo mode)
final useMockDataProvider = StateProvider<bool>((ref) => true);

/// Neighborhoods list provider
final neighborhoodsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final useMock = ref.watch(useMockDataProvider);
  
  if (useMock) {
    return ref.read(mockDataServiceProvider).getNeighborhoods();
  }
  
  try {
    return await ref.read(apiServiceProvider).getNeighborhoods();
  } catch (e) {
    // Fall back to mock data on error
    return ref.read(mockDataServiceProvider).getNeighborhoods();
  }
});

/// Grids provider - fetches grids based on selected neighborhood and category
final gridsProvider = FutureProvider<List<Grid>>((ref) async {
  final neighborhood = ref.watch(selectedNeighborhoodProvider);
  final category = ref.watch(selectedCategoryProvider);
  final useMock = ref.watch(useMockDataProvider);
  
  if (neighborhood == null) {
    return [];
  }
  
  if (useMock) {
    return ref.read(mockDataServiceProvider).getGrids(
      neighborhood: neighborhood,
      category: category,
    );
  }
  
  try {
    return await ref.read(apiServiceProvider).getGrids(
      neighborhood: neighborhood,
      category: category,
    );
  } catch (e) {
    // Fall back to mock data on error
    return ref.read(mockDataServiceProvider).getGrids(
      neighborhood: neighborhood,
      category: category,
    );
  }
});

/// Recommendations provider
final recommendationsProvider = FutureProvider<List<Recommendation>>((ref) async {
  final neighborhood = ref.watch(selectedNeighborhoodProvider);
  final category = ref.watch(selectedCategoryProvider);
  final useMock = ref.watch(useMockDataProvider);
  
  if (neighborhood == null) {
    return [];
  }
  
  if (useMock) {
    return ref.read(mockDataServiceProvider).getRecommendations(
      neighborhood: neighborhood,
      category: category,
      limit: 3,
    );
  }
  
  try {
    return await ref.read(apiServiceProvider).getRecommendations(
      neighborhood: neighborhood,
      category: category,
      limit: 3,
    );
  } catch (e) {
    // Fall back to mock data on error
    return ref.read(mockDataServiceProvider).getRecommendations(
      neighborhood: neighborhood,
      category: category,
      limit: 3,
    );
  }
});

/// Grid detail provider - fetches details for a specific grid
final gridDetailProvider = FutureProvider.family<GridDetail?, String>((ref, gridId) async {
  final category = ref.watch(selectedCategoryProvider);
  final useMock = ref.watch(useMockDataProvider);
  
  if (useMock) {
    return ref.read(mockDataServiceProvider).getGridDetail(
      gridId: gridId,
      category: category,
    );
  }
  
  try {
    return await ref.read(apiServiceProvider).getGridDetail(
      gridId: gridId,
      category: category,
    );
  } catch (e) {
    // Fall back to mock data on error
    return ref.read(mockDataServiceProvider).getGridDetail(
      gridId: gridId,
      category: category,
    );
  }
});

/// Loading state provider
final isLoadingProvider = StateProvider<bool>((ref) => false);

/// Error message provider
final errorMessageProvider = StateProvider<String?>((ref) => null);

/// Submit feedback provider
final submitFeedbackProvider = Provider<Future<bool> Function(String gridId, int rating, String? comment)>((ref) {
  return (String gridId, int rating, String? comment) async {
    final category = ref.read(selectedCategoryProvider);
    final useMock = ref.read(useMockDataProvider);
    
    if (useMock) {
      // Simulate successful feedback in mock mode
      await Future.delayed(const Duration(milliseconds: 500));
      return true;
    }
    
    try {
      await ref.read(apiServiceProvider).submitFeedback(
        gridId: gridId,
        category: category,
        rating: rating,
        comment: comment,
      );
      return true;
    } catch (e) {
      return false;
    }
  };
});

/// Refresh data provider - invalidates all data providers
final refreshDataProvider = Provider<void Function()>((ref) {
  return () {
    ref.invalidate(neighborhoodsProvider);
    ref.invalidate(gridsProvider);
    ref.invalidate(recommendationsProvider);
  };
});
