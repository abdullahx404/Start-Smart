import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../utils/constants.dart';

/// Currently selected category (Gym or Cafe)
final selectedCategoryProvider = StateProvider<String>((ref) {
  return Categories.gym; // Default to Gym
});

/// Currently selected neighborhood ID
final selectedNeighborhoodProvider = StateProvider<String?>((ref) {
  return null;
});

/// Currently selected grid ID (for highlighting on map)
final selectedGridIdProvider = StateProvider<String?>((ref) {
  return null;
});

/// Whether the filter panel is expanded
final filterPanelExpandedProvider = StateProvider<bool>((ref) {
  return false;
});

/// Whether to show the recommendations panel
final showRecommendationsPanelProvider = StateProvider<bool>((ref) {
  return true;
});

/// Search query for filtering grids
final searchQueryProvider = StateProvider<String>((ref) {
  return '';
});

/// Minimum GOS filter value
final minGOSFilterProvider = StateProvider<double>((ref) {
  return 0.0;
});

/// Maximum GOS filter value
final maxGOSFilterProvider = StateProvider<double>((ref) {
  return 1.0;
});

/// Whether to show only high opportunity grids
final showHighOpportunityOnlyProvider = StateProvider<bool>((ref) {
  return false;
});

/// Map zoom level
final mapZoomProvider = StateProvider<double>((ref) {
  return MapConstants.defaultZoom;
});

/// Map center coordinates [lat, lon]
final mapCenterProvider = StateProvider<List<double>>((ref) {
  return [MapConstants.karachiLat, MapConstants.karachiLon];
});

/// Clear all selections
final clearSelectionsProvider = Provider<void Function()>((ref) {
  return () {
    ref.read(selectedGridIdProvider.notifier).state = null;
    ref.read(selectedNeighborhoodProvider.notifier).state = null;
    ref.read(searchQueryProvider.notifier).state = '';
    ref.read(minGOSFilterProvider.notifier).state = 0.0;
    ref.read(maxGOSFilterProvider.notifier).state = 1.0;
    ref.read(showHighOpportunityOnlyProvider.notifier).state = false;
  };
});

/// Helper provider to check if any filters are active
final hasActiveFiltersProvider = Provider<bool>((ref) {
  final minGOS = ref.watch(minGOSFilterProvider);
  final maxGOS = ref.watch(maxGOSFilterProvider);
  final searchQuery = ref.watch(searchQueryProvider);
  final showHighOnly = ref.watch(showHighOpportunityOnlyProvider);
  
  return minGOS > 0.0 || 
         maxGOS < 1.0 || 
         searchQuery.isNotEmpty || 
         showHighOnly;
});

/// Derived provider: Get display name for selected neighborhood
final selectedNeighborhoodNameProvider = Provider<String?>((ref) {
  final neighborhoodId = ref.watch(selectedNeighborhoodProvider);
  if (neighborhoodId == null) return null;
  return Neighborhoods.getDisplayName(neighborhoodId);
});

/// Derived provider: Get icon for selected category
final selectedCategoryIconProvider = Provider<String>((ref) {
  final category = ref.watch(selectedCategoryProvider);
  return Categories.getIcon(category);
});
