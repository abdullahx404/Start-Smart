import 'package:flutter/material.dart';
import '../models/recommendation.dart';
import '../utils/colors.dart';

/// Card widget displaying a single recommendation
class RecommendationCard extends StatelessWidget {
  final Recommendation recommendation;
  final int rank;
  final bool isSelected;
  final VoidCallback onTap;
  final VoidCallback onViewDetails;

  const RecommendationCard({
    super.key,
    required this.recommendation,
    required this.rank,
    this.isSelected = false,
    required this.onTap,
    required this.onViewDetails,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: isSelected ? 4 : 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: isSelected
            ? BorderSide(color: AppColors.primary, width: 2)
            : BorderSide.none,
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header row
              Row(
                children: [
                  _buildRankBadge(),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _formatGridId(recommendation.gridId),
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        Text(
                          _extractNeighborhood(recommendation.gridId),
                          style: TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  _buildGOSBadge(),
                ],
              ),
              const SizedBox(height: 12),

              // Rationale
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.surfaceVariant.withValues(alpha: 0.5),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.lightbulb_outline,
                      size: 16,
                      color: AppColors.warning,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        recommendation.rationale,
                        style: const TextStyle(
                          fontSize: 13,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),

              // Metrics row
              Row(
                children: [
                  _buildMetricChip(
                    Icons.trending_up,
                    '${recommendation.totalDemand}',
                    'Demand',
                    AppColors.info,
                  ),
                  const SizedBox(width: 8),
                  _buildMetricChip(
                    Icons.store,
                    '${recommendation.businessCount}',
                    'Competitors',
                    AppColors.warning,
                  ),
                  const Spacer(),
                  _buildConfidenceBadge(),
                ],
              ),
              const SizedBox(height: 12),

              // Action button
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: onViewDetails,
                  icon: const Icon(Icons.visibility, size: 18),
                  label: const Text('View Details'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.primary,
                    side: BorderSide(
                      color: AppColors.primary.withValues(alpha: 0.5),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRankBadge() {
    final badgeColor = rank == 1
        ? const Color(0xFFFFD700)
        : rank == 2
        ? const Color(0xFFC0C0C0)
        : const Color(0xFFCD7F32);

    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: badgeColor.withValues(alpha: 0.2),
        shape: BoxShape.circle,
        border: Border.all(color: badgeColor, width: 2),
      ),
      child: Center(
        child: Text(
          '#$rank',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: badgeColor.withValues(alpha: 1.0),
            fontSize: 14,
          ),
        ),
      ),
    );
  }

  Widget _buildGOSBadge() {
    final gosColor = AppColors.getGOSColor(recommendation.gos);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: gosColor.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: gosColor.withValues(alpha: 0.5)),
      ),
      child: Column(
        children: [
          Text(
            'GOS',
            style: TextStyle(
              fontSize: 10,
              color: gosColor,
              fontWeight: FontWeight.w500,
            ),
          ),
          Text(
            recommendation.gos.toStringAsFixed(2),
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: gosColor,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConfidenceBadge() {
    final confColor = AppColors.getConfidenceColor(recommendation.confidence);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: confColor.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.verified, size: 14, color: confColor),
          const SizedBox(width: 4),
          Text(
            '${(recommendation.confidence * 100).toInt()}%',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: confColor,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricChip(
    IconData icon,
    String value,
    String label,
    Color color,
  ) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          const SizedBox(width: 2),
          Text(
            label,
            style: TextStyle(fontSize: 10, color: color.withValues(alpha: 0.8)),
          ),
        ],
      ),
    );
  }

  String _formatGridId(String gridId) {
    // Extract cell number: "DHA-Phase2-Cell-01" -> "Cell 01"
    final parts = gridId.split('-');
    if (parts.length >= 2) {
      final cellPart = parts.sublist(parts.length - 2).join(' ');
      return cellPart.replaceAll('-', ' ');
    }
    return gridId;
  }

  String _extractNeighborhood(String gridId) {
    final parts = gridId.split('-Cell-');
    if (parts.isNotEmpty) {
      return parts[0].replaceAll('-', ' ');
    }
    return '';
  }
}

/// Compact recommendation list item
class RecommendationListItem extends StatelessWidget {
  final Recommendation recommendation;
  final int rank;
  final bool isSelected;
  final VoidCallback onTap;

  const RecommendationListItem({
    super.key,
    required this.recommendation,
    required this.rank,
    this.isSelected = false,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final gosColor = AppColors.getGOSColor(recommendation.gos);

    return ListTile(
      onTap: onTap,
      selected: isSelected,
      leading: CircleAvatar(
        backgroundColor: gosColor.withValues(alpha: 0.2),
        child: Text(
          '#$rank',
          style: TextStyle(color: gosColor, fontWeight: FontWeight.bold),
        ),
      ),
      title: Text(
        _formatGridId(recommendation.gridId),
        style: const TextStyle(fontWeight: FontWeight.w600),
      ),
      subtitle: Text(
        recommendation.rationale,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(fontSize: 12),
      ),
      trailing: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: gosColor.withValues(alpha: 0.15),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Text(
          recommendation.gos.toStringAsFixed(2),
          style: TextStyle(fontWeight: FontWeight.bold, color: gosColor),
        ),
      ),
    );
  }

  String _formatGridId(String gridId) {
    final parts = gridId.split('-');
    if (parts.length >= 2) {
      return parts.sublist(parts.length - 2).join(' ').replaceAll('-', ' ');
    }
    return gridId;
  }
}
