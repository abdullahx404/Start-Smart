import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import '../models/grid.dart';
import '../providers/data_provider.dart';
import '../providers/selection_provider.dart';
import '../utils/colors.dart';
import '../utils/constants.dart';
import '../widgets/heatmap_overlay.dart';
import '../widgets/recommendation_card.dart';
import '../widgets/filter_panel.dart';
import 'grid_detail_screen.dart';

/// Main map screen with heatmap overlay and recommendations
class MapScreen extends ConsumerStatefulWidget {
  const MapScreen({super.key});

  @override
  ConsumerState<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends ConsumerState<MapScreen>
    with SingleTickerProviderStateMixin {
  final MapController _mapController = MapController();
  Grid? _selectedGrid;
  bool _showRecommendationsPanel = true;
  bool _isRefreshing = false;
  late AnimationController _panelAnimationController;
  late Animation<double> _panelSlideAnimation;

  @override
  void initState() {
    super.initState();
    _panelAnimationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _panelSlideAnimation = Tween<double>(begin: 1.0, end: 0.0).animate(
      CurvedAnimation(
        parent: _panelAnimationController,
        curve: Curves.easeInOut,
      ),
    );
    if (_showRecommendationsPanel) {
      _panelAnimationController.forward();
    }
  }

  @override
  void dispose() {
    _panelAnimationController.dispose();
    super.dispose();
  }

  Future<void> _refreshData() async {
    setState(() => _isRefreshing = true);
    ref.invalidate(gridsProvider);
    ref.invalidate(recommendationsProvider);
    // Allow UI to update
    await Future.delayed(const Duration(milliseconds: 500));
    setState(() => _isRefreshing = false);
  }

  @override
  Widget build(BuildContext context) {
    final selectedNeighborhood = ref.watch(selectedNeighborhoodProvider);
    final selectedCategory = ref.watch(selectedCategoryProvider);
    final gridsAsync = ref.watch(gridsProvider);
    final recommendationsAsync = ref.watch(recommendationsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          selectedNeighborhood != null
              ? Neighborhoods.getDisplayName(selectedNeighborhood)
              : 'StartSmart',
        ),
        actions: [
          // Category badge
          Container(
            margin: const EdgeInsets.only(right: 8),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: AppColors.surface.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(Categories.getIcon(selectedCategory)),
                const SizedBox(width: 4),
                Text(selectedCategory, style: const TextStyle(fontSize: 14)),
              ],
            ),
          ),
          // Toggle recommendations panel
          IconButton(
            icon: AnimatedSwitcher(
              duration: const Duration(milliseconds: 200),
              child: Icon(
                _showRecommendationsPanel
                    ? Icons.view_sidebar
                    : Icons.view_sidebar_outlined,
                key: ValueKey(_showRecommendationsPanel),
              ),
            ),
            onPressed: () {
              setState(() {
                _showRecommendationsPanel = !_showRecommendationsPanel;
              });
              if (_showRecommendationsPanel) {
                _panelAnimationController.forward();
              } else {
                _panelAnimationController.reverse();
              }
            },
            tooltip: 'Toggle Recommendations',
          ),
          // Refresh button
          IconButton(
            icon: _isRefreshing
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.refresh),
            onPressed: _isRefreshing ? null : _refreshData,
            tooltip: 'Refresh Data',
          ),
        ],
      ),
      body: Stack(
        children: [
          // Map
          gridsAsync.when(
            data: (grids) => _buildMap(grids),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (err, stack) => _buildErrorState(err.toString()),
          ),

          // Filter panel (top left)
          Positioned(
            top: 16,
            left: 16,
            right: _showRecommendationsPanel ? null : 16,
            width: _showRecommendationsPanel ? 280 : null,
            child: const FilterPanel(),
          ),

          // GOS Legend (bottom left)
          const Positioned(bottom: 16, left: 16, child: GOSLegend()),

          // Selected grid popup
          if (_selectedGrid != null)
            Positioned(
              bottom: 100,
              left: 16,
              right: _showRecommendationsPanel ? 340 : 16,
              child: GridInfoPopup(
                grid: _selectedGrid!,
                onClose: () {
                  setState(() {
                    _selectedGrid = null;
                  });
                  ref.read(selectedGridIdProvider.notifier).state = null;
                },
                onViewDetails: () =>
                    _navigateToGridDetail(_selectedGrid!.gridId),
              ),
            ),

          // Recommendations panel (right side) with slide animation
          AnimatedBuilder(
            animation: _panelSlideAnimation,
            builder: (context, child) {
              return Positioned(
                top: 0,
                right: -320 * _panelSlideAnimation.value,
                bottom: 0,
                width: 320,
                child: child!,
              );
            },
            child: Container(
              decoration: BoxDecoration(
                color: AppColors.background,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.1),
                    blurRadius: 8,
                    offset: const Offset(-2, 0),
                  ),
                ],
              ),
              child: recommendationsAsync.when(
                data: (recommendations) =>
                    _buildRecommendationsPanel(recommendations),
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (err, stack) => Center(child: Text('Error: $err')),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMap(List<Grid> grids) {
    // Calculate center based on grids
    LatLng center;
    if (grids.isNotEmpty) {
      final avgLat =
          grids.map((g) => g.latCenter).reduce((a, b) => a + b) / grids.length;
      final avgLon =
          grids.map((g) => g.lonCenter).reduce((a, b) => a + b) / grids.length;
      center = LatLng(avgLat, avgLon);
    } else {
      center = LatLng(MapConstants.karachiLat, MapConstants.karachiLon);
    }

    return FlutterMap(
      mapController: _mapController,
      options: MapOptions(
        initialCenter: center,
        initialZoom: MapConstants.defaultZoom,
        minZoom: MapConstants.minZoom,
        maxZoom: MapConstants.maxZoom,
        onTap: (tapPosition, point) {
          // Check if tap is within any grid
          for (final grid in grids) {
            if (_isPointInGrid(point, grid)) {
              _onGridTapped(grid);
              return;
            }
          }
          // Clear selection if tapped outside grids
          setState(() {
            _selectedGrid = null;
          });
          ref.read(selectedGridIdProvider.notifier).state = null;
        },
      ),
      children: [
        // Base map tiles
        TileLayer(
          urlTemplate: MapConstants.tileUrlTemplate,
          userAgentPackageName: MapConstants.tileUserAgent,
        ),

        // Heatmap overlay
        if (grids.isNotEmpty)
          InteractiveGridLayer(
            grids: grids,
            selectedGridId: _selectedGrid?.gridId,
            onGridTap: _onGridTapped,
          ),
      ],
    );
  }

  Widget _buildRecommendationsPanel(List<dynamic> recommendations) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Header
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.surface,
            border: Border(bottom: BorderSide(color: AppColors.surfaceVariant)),
          ),
          child: Row(
            children: [
              const Icon(Icons.star, color: AppColors.warning),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  'Top Recommendations',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                ),
              ),
              Text(
                '${recommendations.length} found',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 12),
              ),
            ],
          ),
        ),

        // Recommendations list
        Expanded(
          child: recommendations.isEmpty
              ? _buildEmptyRecommendations()
              : ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: recommendations.length,
                  itemBuilder: (context, index) {
                    final recommendation = recommendations[index];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: RecommendationCard(
                        recommendation: recommendation,
                        rank: index + 1,
                        isSelected:
                            _selectedGrid?.gridId == recommendation.gridId,
                        onTap: () => _onRecommendationTapped(recommendation),
                        onViewDetails: () =>
                            _navigateToGridDetail(recommendation.gridId),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildEmptyRecommendations() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.search_off, size: 64, color: AppColors.textHint),
            const SizedBox(height: 16),
            Text(
              'No recommendations yet',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Select a neighborhood and category to see top locations',
              style: TextStyle(color: AppColors.textHint, fontSize: 13),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorState(String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline, size: 64, color: AppColors.error),
            const SizedBox(height: 16),
            Text(
              'Unable to load data',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: AppColors.error,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              error,
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: () {
                ref.invalidate(gridsProvider);
                ref.invalidate(recommendationsProvider);
              },
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  void _onGridTapped(Grid grid) {
    setState(() {
      _selectedGrid = grid;
    });
    ref.read(selectedGridIdProvider.notifier).state = grid.gridId;

    // Animate to grid
    _mapController.move(grid.center, _mapController.camera.zoom);
  }

  void _onRecommendationTapped(dynamic recommendation) {
    // Find the grid in the list or create a temporary one
    final gridsAsync = ref.read(gridsProvider);
    gridsAsync.whenData((grids) {
      final grid = grids.firstWhere(
        (g) => g.gridId == recommendation.gridId,
        orElse: () => Grid(
          gridId: recommendation.gridId,
          neighborhood: '',
          latCenter: recommendation.latCenter,
          lonCenter: recommendation.lonCenter,
          latNorth: recommendation.latCenter + 0.0045,
          latSouth: recommendation.latCenter - 0.0045,
          lonEast: recommendation.lonCenter + 0.005,
          lonWest: recommendation.lonCenter - 0.005,
          gos: recommendation.gos,
          confidence: recommendation.confidence,
          businessCount: recommendation.businessCount,
          instagramVolume: recommendation.instagramVolume,
          redditMentions: recommendation.redditMentions,
        ),
      );
      _onGridTapped(grid);
    });
  }

  void _navigateToGridDetail(String gridId) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => GridDetailScreen(gridId: gridId)),
    );
  }

  bool _isPointInGrid(LatLng point, Grid grid) {
    return point.latitude >= grid.latSouth &&
        point.latitude <= grid.latNorth &&
        point.longitude >= grid.lonWest &&
        point.longitude <= grid.lonEast;
  }
}
