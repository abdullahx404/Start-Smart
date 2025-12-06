import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import '../models/grid.dart';
import '../utils/colors.dart';

/// Heatmap overlay widget for displaying GOS scores on the map
class HeatmapOverlay extends StatelessWidget {
  final List<Grid> grids;
  final String? selectedGridId;
  final Function(Grid)? onGridTap;
  final double opacity;

  const HeatmapOverlay({
    super.key,
    required this.grids,
    this.selectedGridId,
    this.onGridTap,
    this.opacity = 0.6,
  });

  @override
  Widget build(BuildContext context) {
    return PolygonLayer(
      polygons: grids.map((grid) => _buildGridPolygon(grid)).toList(),
    );
  }

  Polygon _buildGridPolygon(Grid grid) {
    final isSelected = grid.gridId == selectedGridId;
    final color = AppColors.getGOSColorWithOpacity(grid.gos, opacity: opacity);

    return Polygon(
      points: grid.boundingBox,
      color: color,
      borderColor: isSelected
          ? AppColors.gridBorderSelected
          : AppColors.gridBorder.withValues(alpha: 0.5),
      borderStrokeWidth: isSelected ? 3.0 : 1.0,
      isFilled: true,
    );
  }
}

/// Interactive grid layer with tap detection
class InteractiveGridLayer extends StatelessWidget {
  final List<Grid> grids;
  final String? selectedGridId;
  final Function(Grid) onGridTap;
  final double opacity;

  const InteractiveGridLayer({
    super.key,
    required this.grids,
    required this.onGridTap,
    this.selectedGridId,
    this.opacity = 0.6,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Heatmap polygons
        PolygonLayer(
          polygons: grids.map((grid) => _buildGridPolygon(grid)).toList(),
        ),
        // Invisible tap targets with gesture detection
        ...grids.map((grid) => _buildTapTarget(context, grid)),
      ],
    );
  }

  Polygon _buildGridPolygon(Grid grid) {
    final isSelected = grid.gridId == selectedGridId;
    final color = AppColors.getGOSColorWithOpacity(grid.gos, opacity: opacity);

    return Polygon(
      points: grid.boundingBox,
      color: color,
      borderColor: isSelected
          ? AppColors.gridBorderSelected
          : AppColors.gridBorder.withValues(alpha: 0.5),
      borderStrokeWidth: isSelected ? 3.0 : 1.0,
      isFilled: true,
    );
  }

  Widget _buildTapTarget(BuildContext context, Grid grid) {
    return MarkerLayer(
      markers: [
        Marker(
          point: grid.center,
          width: 60,
          height: 40,
          child: GestureDetector(
            onTap: () => onGridTap(grid),
            child: Container(
              decoration: BoxDecoration(
                color: Colors.transparent,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Center(child: _buildGOSBadge(grid)),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildGOSBadge(Grid grid) {
    final isSelected = grid.gridId == selectedGridId;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: isSelected
            ? AppColors.secondary
            : AppColors.surface.withValues(alpha: 0.9),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(
          color: isSelected
              ? AppColors.secondaryDark
              : AppColors.gridBorder.withValues(alpha: 0.3),
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.2),
            blurRadius: 2,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Text(
        grid.gos.toStringAsFixed(2),
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.bold,
          color: isSelected
              ? AppColors.textOnPrimary
              : AppColors.getGOSColor(grid.gos),
        ),
      ),
    );
  }
}

/// GOS Legend widget
class GOSLegend extends StatelessWidget {
  const GOSLegend({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface.withValues(alpha: 0.95),
        borderRadius: BorderRadius.circular(8),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Opportunity Score',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
          ),
          const SizedBox(height: 8),
          _buildLegendItem('High (0.7-1.0)', AppColors.gosVeryHigh),
          _buildLegendItem('Good (0.5-0.7)', AppColors.gosHigh),
          _buildLegendItem('Medium (0.3-0.5)', AppColors.gosMedium),
          _buildLegendItem('Low (0.1-0.3)', AppColors.gosLow),
          _buildLegendItem('Very Low (0-0.1)', AppColors.gosVeryLow),
        ],
      ),
    );
  }

  Widget _buildLegendItem(String label, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 16,
            height: 16,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.7),
              borderRadius: BorderRadius.circular(2),
              border: Border.all(color: color, width: 1),
            ),
          ),
          const SizedBox(width: 8),
          Text(label, style: const TextStyle(fontSize: 11)),
        ],
      ),
    );
  }
}

/// Compact GOS gradient bar for smaller spaces
class GOSGradientBar extends StatelessWidget {
  final double width;
  final double height;

  const GOSGradientBar({super.key, this.width = 150, this.height = 12});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: width,
          height: height,
          decoration: BoxDecoration(
            gradient: LinearGradient(colors: AppColors.gosGradient),
            borderRadius: BorderRadius.circular(4),
          ),
        ),
        const SizedBox(height: 4),
        SizedBox(
          width: width,
          child: const Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Low', style: TextStyle(fontSize: 10)),
              Text('High', style: TextStyle(fontSize: 10)),
            ],
          ),
        ),
      ],
    );
  }
}

/// Grid info popup shown when a grid is selected
class GridInfoPopup extends StatelessWidget {
  final Grid grid;
  final VoidCallback onClose;
  final VoidCallback onViewDetails;

  const GridInfoPopup({
    super.key,
    required this.grid,
    required this.onClose,
    required this.onViewDetails,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.15),
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Expanded(
                child: Text(
                  grid.gridId.split('-').last, // Just show "Cell-01" part
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close, size: 20),
                onPressed: onClose,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
              ),
            ],
          ),
          const SizedBox(height: 8),

          // GOS Score
          Row(
            children: [
              _buildScoreBadge(
                'GOS',
                grid.gos,
                AppColors.getGOSColor(grid.gos),
              ),
              const SizedBox(width: 12),
              _buildScoreBadge(
                'Confidence',
                grid.confidence,
                AppColors.getConfidenceColor(grid.confidence),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Quick metrics
          Row(
            children: [
              _buildMetric('📊', '${grid.totalDemand} signals'),
              const SizedBox(width: 16),
              _buildMetric('🏢', '${grid.businessCount} competitors'),
            ],
          ),
          const SizedBox(height: 12),

          // View details button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: onViewDetails,
              child: const Text('View Details'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScoreBadge(String label, double value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withValues(alpha: 0.5)),
      ),
      child: Column(
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 10,
              color: color,
              fontWeight: FontWeight.w500,
            ),
          ),
          Text(
            value.toStringAsFixed(2),
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetric(String icon, String text) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(icon, style: const TextStyle(fontSize: 14)),
        const SizedBox(width: 4),
        Text(text, style: const TextStyle(fontSize: 12)),
      ],
    );
  }
}
