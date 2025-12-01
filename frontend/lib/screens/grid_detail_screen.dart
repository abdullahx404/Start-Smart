import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import '../models/grid_detail.dart';
import '../models/recommendation.dart';
import '../providers/data_provider.dart';
import '../providers/selection_provider.dart';
import '../utils/colors.dart';
import '../utils/constants.dart';

/// Detailed view of a single grid cell
class GridDetailScreen extends ConsumerStatefulWidget {
  final String gridId;

  const GridDetailScreen({super.key, required this.gridId});

  @override
  ConsumerState<GridDetailScreen> createState() => _GridDetailScreenState();
}

class _GridDetailScreenState extends ConsumerState<GridDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  int? _feedbackRating;
  final _feedbackController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _feedbackController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final gridDetailAsync = ref.watch(gridDetailProvider(widget.gridId));
    final selectedCategory = ref.watch(selectedCategoryProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(_formatGridId(widget.gridId)),
        actions: [
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
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppColors.textOnPrimary,
          tabs: const [
            Tab(text: 'Overview', icon: Icon(Icons.dashboard)),
            Tab(text: 'Evidence', icon: Icon(Icons.article)),
            Tab(text: 'Competitors', icon: Icon(Icons.store)),
          ],
        ),
      ),
      body: gridDetailAsync.when(
        data: (detail) => detail != null
            ? TabBarView(
                controller: _tabController,
                children: [
                  _buildOverviewTab(detail),
                  _buildEvidenceTab(detail),
                  _buildCompetitorsTab(detail),
                ],
              )
            : _buildEmptyState(),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => _buildErrorState(err.toString()),
      ),
      bottomNavigationBar: _buildFeedbackBar(),
    );
  }

  Widget _buildOverviewTab(GridDetail detail) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Mini map
          _buildMiniMap(detail),
          const SizedBox(height: 16),

          // GOS Score card
          _buildScoreCard(detail),
          const SizedBox(height: 16),

          // Metrics grid
          _buildMetricsGrid(detail),
          const SizedBox(height: 16),

          // Rationale
          if (detail.rationale != null) _buildRationaleCard(detail.rationale!),
        ],
      ),
    );
  }

  Widget _buildMiniMap(GridDetail detail) {
    final center = LatLng(detail.latCenter, detail.lonCenter);
    final bounds = [
      LatLng(detail.latNorth, detail.lonWest),
      LatLng(detail.latNorth, detail.lonEast),
      LatLng(detail.latSouth, detail.lonEast),
      LatLng(detail.latSouth, detail.lonWest),
    ];

    return Card(
      clipBehavior: Clip.antiAlias,
      child: SizedBox(
        height: 200,
        child: FlutterMap(
          options: MapOptions(
            initialCenter: center,
            initialZoom: MapConstants.gridDetailZoom,
            interactionOptions: const InteractionOptions(
              flags: InteractiveFlag.none,
            ),
          ),
          children: [
            TileLayer(
              urlTemplate: MapConstants.tileUrlTemplate,
              userAgentPackageName: MapConstants.tileUserAgent,
            ),
            PolygonLayer(
              polygons: [
                Polygon(
                  points: bounds,
                  color: AppColors.getGOSColorWithOpacity(detail.gos),
                  borderColor: AppColors.primary,
                  borderStrokeWidth: 3,
                  isFilled: true,
                ),
              ],
            ),
            MarkerLayer(
              markers: [
                Marker(
                  point: center,
                  width: 40,
                  height: 40,
                  child: Container(
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.primary, width: 2),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.2),
                          blurRadius: 4,
                        ),
                      ],
                    ),
                    child: const Center(
                      child: Icon(Icons.location_on, color: AppColors.primary),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildScoreCard(GridDetail detail) {
    final gosColor = AppColors.getGOSColor(detail.gos);
    final confColor = AppColors.getConfidenceColor(detail.confidence);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            // GOS Score
            Expanded(
              child: Column(
                children: [
                  Text(
                    'Opportunity Score',
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 13,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    detail.gos.toStringAsFixed(3),
                    style: TextStyle(
                      fontSize: 42,
                      fontWeight: FontWeight.bold,
                      color: gosColor,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: gosColor.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      detail.opportunityLevel,
                      style: TextStyle(
                        color: gosColor,
                        fontWeight: FontWeight.w600,
                        fontSize: 13,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // Divider
            Container(width: 1, height: 80, color: AppColors.surfaceVariant),

            // Confidence
            Expanded(
              child: Column(
                children: [
                  Text(
                    'Confidence',
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 13,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${(detail.confidence * 100).toInt()}%',
                    style: TextStyle(
                      fontSize: 42,
                      fontWeight: FontWeight.bold,
                      color: confColor,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: confColor.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      detail.confidenceLevel,
                      style: TextStyle(
                        color: confColor,
                        fontWeight: FontWeight.w600,
                        fontSize: 13,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricsGrid(GridDetail detail) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Key Metrics',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _MetricTile(
                    icon: Icons.store,
                    label: 'Competitors',
                    value: '${detail.metrics.businessCount}',
                    subLabel: detail.metrics.competitionLevel,
                    color: AppColors.warning,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _MetricTile(
                    icon: Icons.trending_up,
                    label: 'Demand Signals',
                    value: '${detail.metrics.totalDemand}',
                    subLabel: detail.metrics.demandLevel,
                    color: AppColors.info,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _MetricTile(
                    icon: Icons.camera_alt,
                    label: 'Instagram',
                    value: '${detail.metrics.instagramVolume}',
                    subLabel: 'posts',
                    color: const Color(0xFFE1306C),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _MetricTile(
                    icon: Icons.reddit,
                    label: 'Reddit',
                    value: '${detail.metrics.redditMentions}',
                    subLabel: 'mentions',
                    color: const Color(0xFFFF4500),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRationaleCard(String rationale) {
    return Card(
      color: AppColors.primary.withValues(alpha: 0.05),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(Icons.lightbulb, color: AppColors.warning, size: 32),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Why this location?',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    rationale,
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEvidenceTab(GridDetail detail) {
    if (detail.topPosts.isEmpty) {
      return _buildEmptyTabState(
        icon: Icons.article_outlined,
        title: 'No Evidence Yet',
        subtitle: 'Social media signals will appear here',
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: detail.topPosts.length,
      itemBuilder: (context, index) {
        final post = detail.topPosts[index];
        return _PostCard(post: post);
      },
    );
  }

  Widget _buildCompetitorsTab(GridDetail detail) {
    if (detail.competitors.isEmpty) {
      return _buildEmptyTabState(
        icon: Icons.store_outlined,
        title: 'No Competitors Found',
        subtitle: 'This is a great opportunity - no existing businesses!',
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: detail.competitors.length,
      itemBuilder: (context, index) {
        final competitor = detail.competitors[index];
        return _CompetitorCard(competitor: competitor);
      },
    );
  }

  Widget _buildFeedbackBar() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 8,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        children: [
          const Text(
            'Is this helpful?',
            style: TextStyle(fontWeight: FontWeight.w500),
          ),
          const Spacer(),
          IconButton(
            icon: Icon(
              _feedbackRating == 1 ? Icons.thumb_up : Icons.thumb_up_outlined,
              color: _feedbackRating == 1 ? AppColors.success : null,
            ),
            onPressed: () => _submitFeedback(1),
          ),
          IconButton(
            icon: Icon(
              _feedbackRating == -1
                  ? Icons.thumb_down
                  : Icons.thumb_down_outlined,
              color: _feedbackRating == -1 ? AppColors.error : null,
            ),
            onPressed: () => _submitFeedback(-1),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.error_outline, size: 64, color: AppColors.textHint),
          const SizedBox(height: 16),
          const Text(
            'Grid not found',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState(String error) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.error_outline, size: 64, color: AppColors.error),
          const SizedBox(height: 16),
          Text('Error: $error'),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () => ref.refresh(gridDetailProvider(widget.gridId)),
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyTabState({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 64, color: AppColors.textHint),
          const SizedBox(height: 16),
          Text(
            title,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          Text(subtitle, style: TextStyle(color: AppColors.textSecondary)),
        ],
      ),
    );
  }

  void _submitFeedback(int rating) async {
    setState(() {
      _feedbackRating = rating;
    });

    final submitFeedback = ref.read(submitFeedbackProvider);
    final success = await submitFeedback(widget.gridId, rating, null);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            success ? 'Thanks for your feedback!' : 'Failed to submit feedback',
          ),
          backgroundColor: success ? AppColors.success : AppColors.error,
        ),
      );
    }
  }

  String _formatGridId(String gridId) {
    final parts = gridId.split('-');
    if (parts.length >= 2) {
      return parts.sublist(parts.length - 2).join(' ').replaceAll('-', ' ');
    }
    return gridId;
  }
}

/// Metric tile widget
class _MetricTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final String subLabel;
  final Color color;

  const _MetricTile({
    required this.icon,
    required this.label,
    required this.value,
    required this.subLabel,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 16, color: color),
              const SizedBox(width: 4),
              Text(label, style: TextStyle(fontSize: 12, color: color)),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            subLabel,
            style: TextStyle(fontSize: 11, color: color.withValues(alpha: 0.8)),
          ),
        ],
      ),
    );
  }
}

/// Social post card
class _PostCard extends StatelessWidget {
  final TopPost post;

  const _PostCard({required this.post});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(post.sourceIcon, style: const TextStyle(fontSize: 20)),
                const SizedBox(width: 8),
                Text(
                  post.source.toUpperCase(),
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
                const Spacer(),
                Text(
                  post.formattedTimestamp,
                  style: TextStyle(color: AppColors.textHint, fontSize: 12),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(post.text, style: const TextStyle(fontSize: 14)),
          ],
        ),
      ),
    );
  }
}

/// Competitor card
class _CompetitorCard extends StatelessWidget {
  final Competitor competitor;

  const _CompetitorCard({required this.competitor});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: AppColors.warning.withValues(alpha: 0.2),
          child: const Icon(Icons.store, color: AppColors.warning),
        ),
        title: Text(
          competitor.name,
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Text(competitor.formattedDistance),
        trailing: competitor.rating != null
            ? Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.warning.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.star, size: 16, color: AppColors.warning),
                    const SizedBox(width: 4),
                    Text(
                      competitor.rating!.toStringAsFixed(1),
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              )
            : null,
      ),
    );
  }
}
