import 'package:flutter/material.dart';
import '../models/enhanced_recommendation.dart';
import '../services/api_service.dart';

/// Screen to display full analysis results with aesthetic blue theme
class AnalysisResultsScreen extends StatefulWidget {
  final double latitude;
  final double longitude;
  final int radius;
  final bool isLLMMode;
  final String businessType;

  const AnalysisResultsScreen({
    super.key,
    required this.latitude,
    required this.longitude,
    required this.radius,
    required this.isLLMMode,
    required this.businessType,
  });

  @override
  State<AnalysisResultsScreen> createState() => _AnalysisResultsScreenState();
}

class _AnalysisResultsScreenState extends State<AnalysisResultsScreen>
    with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  bool _isLoading = true;
  EnhancedRecommendation? _recommendation;
  String? _error;
  
  // Animation controllers
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  // Blue theme colors
  static const Color _primaryBlue = Color(0xFF1E40AF);
  static const Color _lightBlue = Color(0xFF3B82F6);
  static const Color _darkBlue = Color(0xFF1E3A8A);
  static const Color _accentBlue = Color(0xFF60A5FA);

  /// Format suitability text to be user-friendly
  String _formatSuitability(String suitability) {
    switch (suitability.toLowerCase()) {
      case 'excellent':
        return '⭐ Excellent';
      case 'good':
        return '✓ Good';
      case 'moderate':
        return '○ Moderate';
      case 'poor':
        return '△ Poor';
      case 'not_recommended':
        return '✗ Low Potential';
      default:
        return suitability.replaceAll('_', ' ');
    }
  }

  /// Get color for suitability level
  Color _getSuitabilityColor(String suitability) {
    switch (suitability.toLowerCase()) {
      case 'excellent':
        return const Color(0xFF10B981);
      case 'good':
        return const Color(0xFF3B82F6);
      case 'moderate':
        return const Color(0xFFF59E0B);
      case 'poor':
        return const Color(0xFFEF4444);
      case 'not_recommended':
        return const Color(0xFF6B7280);
      default:
        return Colors.grey[600]!;
    }
  }

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeOut),
    );
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.1),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _animationController, curve: Curves.easeOutCubic));
    
    _fetchRecommendation();
  }

  @override
  void dispose() {
    _animationController.dispose();
    _apiService.dispose();
    super.dispose();
  }

  Future<void> _fetchRecommendation() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final recommendation = widget.isLLMMode
          ? await _apiService.getLLMRecommendation(
              lat: widget.latitude,
              lon: widget.longitude,
              radius: widget.radius,
            )
          : await _apiService.getFastRecommendation(
              lat: widget.latitude,
              lon: widget.longitude,
              radius: widget.radius,
            );

      setState(() {
        _recommendation = recommendation;
        _isLoading = false;
      });
      _animationController.forward();
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [_primaryBlue, _darkBlue],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              _buildAppBar(),
              Expanded(child: _buildBody()),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAppBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () => Navigator.pop(context),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Analysis Results',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'For ${widget.businessType} in Clifton',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.8),
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),
          if (!_isLoading && _recommendation != null)
            Container(
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: IconButton(
                icon: const Icon(Icons.refresh, color: Colors.white),
                onPressed: _fetchRecommendation,
                tooltip: 'Refresh Analysis',
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return _buildLoadingState();
    }

    if (_error != null) {
      return _buildErrorState();
    }

    if (_recommendation == null) {
      return _buildErrorState();
    }

    return _buildResultsView(_recommendation!);
  }

  Widget _buildLoadingState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Animated loading indicator with pulsing effect
          TweenAnimationBuilder<double>(
            tween: Tween(begin: 0.8, end: 1.2),
            duration: const Duration(milliseconds: 1000),
            curve: Curves.easeInOut,
            builder: (context, scale, child) {
              return Transform.scale(
                scale: scale,
                child: Container(
                  width: 100,
                  height: 100,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(
                      colors: [_accentBlue, _lightBlue],
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: _accentBlue.withOpacity(0.4),
                        blurRadius: 20,
                        spreadRadius: 5,
                      ),
                    ],
                  ),
                  child: Center(
                    child: Icon(
                      widget.businessType == 'Gym' 
                          ? Icons.fitness_center 
                          : Icons.coffee,
                      size: 48,
                      color: Colors.white,
                    ),
                  ),
                ),
              );
            },
            onEnd: () => setState(() {}), // Restart animation
          ),
          const SizedBox(height: 40),
          
          // Loading text with animation
          Text(
            widget.isLLMMode
                ? 'AI is analyzing this location...'
                : 'Quick analysis in progress...',
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            widget.isLLMMode
                ? 'This may take 5-15 seconds'
                : 'This takes about 1-2 seconds',
            style: TextStyle(
              fontSize: 16,
              color: Colors.white.withOpacity(0.7),
            ),
          ),
          const SizedBox(height: 32),
          
          // Progress bar
          Container(
            width: 200,
            height: 6,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(3),
            ),
            child: LayoutBuilder(
              builder: (context, constraints) {
                return TweenAnimationBuilder<double>(
                  tween: Tween(begin: 0, end: 1),
                  duration: Duration(seconds: widget.isLLMMode ? 12 : 2),
                  curve: Curves.easeInOut,
                  builder: (context, value, child) {
                    return Align(
                      alignment: Alignment.centerLeft,
                      child: Container(
                        width: constraints.maxWidth * value,
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [_accentBlue, Colors.white],
                          ),
                          borderRadius: BorderRadius.circular(3),
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
          const SizedBox(height: 40),
          
          // Location info card
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 40),
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white.withOpacity(0.2)),
            ),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.location_on, size: 20, color: Colors.white),
                    const SizedBox(width: 8),
                    Text(
                      'Clifton, Karachi',
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                        fontSize: 16,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _buildInfoChip(Icons.radar, '${widget.radius}m'),
                    const SizedBox(width: 16),
                    _buildInfoChip(
                      widget.isLLMMode ? Icons.psychology : Icons.bolt,
                      widget.isLLMMode ? 'AI Mode' : 'Fast Mode',
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoChip(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: Colors.white),
          const SizedBox(width: 6),
          Text(
            label,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w500,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 100,
              height: 100,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.red.withOpacity(0.2),
              ),
              child: const Icon(Icons.error_outline, size: 48, color: Colors.white),
            ),
            const SizedBox(height: 24),
            const Text(
              'Analysis Failed',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              _error ?? 'An unknown error occurred',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white.withOpacity(0.7)),
            ),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                OutlinedButton.icon(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.arrow_back, color: Colors.white),
                  label: const Text('Go Back', style: TextStyle(color: Colors.white)),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Colors.white),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  ),
                ),
                const SizedBox(width: 16),
                ElevatedButton.icon(
                  onPressed: _fetchRecommendation,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Retry'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: _primaryBlue,
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResultsView(EnhancedRecommendation rec) {
    // Get the score for the selected business type
    final selectedScore = widget.businessType.toLowerCase() == 'gym' 
        ? rec.gym 
        : rec.cafe;
    final isGoodChoice = widget.businessType.toLowerCase() == rec.recommendation.bestCategory.toLowerCase();

    return FadeTransition(
      opacity: _fadeAnimation,
      child: SlideTransition(
        position: _slideAnimation,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 1. FIRST: Show nearby businesses in the area
              if (rec.bev != null) ...[
                _buildNearbyBusinessesCard(rec.bev!),
                const SizedBox(height: 20),
              ],

              // 2. GYM vs CAFE Comparison Card - Shows BOTH with scores
              _buildComparisonCard(rec),
              const SizedBox(height: 20),

              // 3. Why one is better than the other (detailed reasoning)
              _buildWhyBetterCard(rec, isGoodChoice),
              const SizedBox(height: 20),

              // 4. LLM insights with full reasoning (if available)
              if (rec.llmInsights != null) ...[
                _buildInsightsCard(rec.llmInsights!),
                const SizedBox(height: 20),
              ],

              // 5. Processing info footer
              _buildProcessingInfo(rec),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  /// Card comparing Gym vs Cafe with confidence scores for both
  Widget _buildComparisonCard(EnhancedRecommendation rec) {
    final gymScore = rec.gym;
    final cafeScore = rec.cafe;
    final gymPercent = (gymScore.score * 100).toInt();
    final cafePercent = (cafeScore.score * 100).toInt();
    final gymIsBetter = gymScore.score >= cafeScore.score;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.compare_arrows, color: _primaryBlue),
                const SizedBox(width: 8),
                const Text(
                  'Business Type Comparison',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),

            // GYM Score
            _buildBusinessTypeRow(
              icon: Icons.fitness_center,
              name: 'GYM',
              score: gymPercent,
              suitability: gymScore.suitability,
              isSelected: widget.businessType.toLowerCase() == 'gym',
              isBetter: gymIsBetter,
              color: const Color(0xFF10B981),
            ),
            const SizedBox(height: 16),

            // VS Divider
            Row(
              children: [
                Expanded(child: Divider(color: Colors.grey[300])),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Text(
                    'VS',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.grey[500],
                      fontSize: 14,
                    ),
                  ),
                ),
                Expanded(child: Divider(color: Colors.grey[300])),
              ],
            ),
            const SizedBox(height: 16),

            // CAFE Score
            _buildBusinessTypeRow(
              icon: Icons.coffee,
              name: 'CAFE',
              score: cafePercent,
              suitability: cafeScore.suitability,
              isSelected: widget.businessType.toLowerCase() == 'cafe',
              isBetter: !gymIsBetter,
              color: const Color(0xFF8B5CF6),
            ),

            const SizedBox(height: 20),

            // Winner announcement
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: gymIsBetter 
                      ? [const Color(0xFF10B981), const Color(0xFF059669)]
                      : [const Color(0xFF8B5CF6), const Color(0xFF7C3AED)],
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  Icon(
                    gymIsBetter ? Icons.fitness_center : Icons.coffee,
                    color: Colors.white,
                    size: 24,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${gymIsBetter ? "GYM" : "CAFE"} is recommended for this location',
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 15,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${((gymIsBetter ? gymScore.score : cafeScore.score) * 100).toInt()}% confidence score',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.9),
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Icon(Icons.verified, color: Colors.white),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBusinessTypeRow({
    required IconData icon,
    required String name,
    required int score,
    required String suitability,
    required bool isSelected,
    required bool isBetter,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isSelected 
            ? _primaryBlue.withOpacity(0.1)
            : Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isSelected ? _primaryBlue : Colors.grey[200]!,
          width: isSelected ? 2 : 1,
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      name,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    if (isSelected) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: _primaryBlue,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Text(
                          'Your Choice',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                    if (isBetter) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: const Color(0xFF10B981),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Text(
                          'RECOMMENDED',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  _formatSuitability(suitability),
                  style: TextStyle(
                    color: _getSuitabilityColor(suitability),
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
          // Score circle
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: isBetter 
                    ? [color, color.withOpacity(0.7)]
                    : [Colors.grey[400]!, Colors.grey[300]!],
              ),
            ),
            child: Center(
              child: Text(
                '$score%',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Card explaining why one option is better than the other
  Widget _buildWhyBetterCard(EnhancedRecommendation rec, bool isGoodChoice) {
    final gymScore = rec.gym;
    final cafeScore = rec.cafe;
    final gymIsBetter = gymScore.score >= cafeScore.score;
    final userSelectedGym = widget.businessType.toLowerCase() == 'gym';

    final betterOption = gymIsBetter ? 'Gym' : 'Cafe';
    final betterScore = gymIsBetter ? gymScore : cafeScore;
    final worseScore = gymIsBetter ? cafeScore : gymScore;
    final worseOption = gymIsBetter ? 'Cafe' : 'Gym';

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.lightbulb, color: _primaryBlue),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Why $betterOption is Better Here',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Positive factors for the better option
            if (betterScore.positiveFactors.isNotEmpty) ...[
              const Text(
                '✅ Reasons for Success:',
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14, color: Color(0xFF10B981)),
              ),
              const SizedBox(height: 8),
              ...betterScore.positiveFactors.map((factor) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.check_circle, color: Color(0xFF10B981), size: 18),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        factor,
                        style: TextStyle(color: Colors.grey[700], fontSize: 14),
                      ),
                    ),
                  ],
                ),
              )),
              const SizedBox(height: 16),
            ],

            // Concerns about the worse option
            if (worseScore.concerns.isNotEmpty) ...[
              Text(
                '⚠️ Why $worseOption Scores Lower:',
                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14, color: Color(0xFFF59E0B)),
              ),
              const SizedBox(height: 8),
              ...worseScore.concerns.map((concern) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.warning_amber, color: Color(0xFFF59E0B), size: 18),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        concern,
                        style: TextStyle(color: Colors.grey[700], fontSize: 14),
                      ),
                    ),
                  ],
                ),
              )),
              const SizedBox(height: 16),
            ],

            // If user selected the worse option, show advice
            if (!isGoodChoice) ...[
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFFFEF3C7),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFF59E0B)),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.info, color: Color(0xFFF59E0B)),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'You selected ${widget.businessType}',
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF92400E),
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'While ${widget.businessType} is possible here, a $betterOption would have ${((betterScore.score - worseScore.score) * 100).toInt()}% higher success potential based on the area analysis.',
                            style: const TextStyle(
                              color: Color(0xFF92400E),
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ] else ...[
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFFD1FAE5),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF10B981)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.thumb_up, color: Color(0xFF10B981)),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Great choice! ${widget.businessType} is the recommended business type for this location.',
                        style: const TextStyle(
                          color: Color(0xFF065F46),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  /// Card showing existing businesses in the area
  Widget _buildNearbyBusinessesCard(BEVSummary bev) {
    // Build list of business types with their counts
    final List<Map<String, dynamic>> businesses = [
      {'icon': Icons.fitness_center, 'name': 'Gyms', 'count': bev.gymCount, 'color': const Color(0xFF10B981)},
      {'icon': Icons.coffee, 'name': 'Cafes', 'count': bev.cafeCount, 'color': const Color(0xFF8B5CF6)},
      {'icon': Icons.restaurant, 'name': 'Restaurants', 'count': bev.restaurantCount, 'color': const Color(0xFFF59E0B)},
      {'icon': Icons.business, 'name': 'Offices', 'count': bev.officeCount, 'color': const Color(0xFF3B82F6)},
      {'icon': Icons.school, 'name': 'Schools', 'count': bev.schoolCount, 'color': const Color(0xFFEC4899)},
      {'icon': Icons.account_balance, 'name': 'Banks', 'count': bev.bankCount, 'color': const Color(0xFF6366F1)},
      {'icon': Icons.local_hospital, 'name': 'Healthcare', 'count': bev.healthcareCount, 'color': const Color(0xFFEF4444)},
      {'icon': Icons.directions_transit, 'name': 'Transit', 'count': bev.transitCount, 'color': const Color(0xFF14B8A6)},
      {'icon': Icons.park, 'name': 'Parks', 'count': bev.parkCount, 'color': const Color(0xFF22C55E)},
      {'icon': Icons.shopping_bag, 'name': 'Malls', 'count': bev.mallCount, 'color': const Color(0xFFF97316)},
    ];

    // Filter to only show businesses that exist in the area
    final existingBusinesses = businesses.where((b) => (b['count'] as int) > 0).toList();

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.location_city, color: _primaryBlue),
                const SizedBox(width: 8),
                const Text(
                  'Available Businesses in This Area',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Total: ${bev.totalBusinesses} businesses • ${bev.incomeLevel}',
              style: TextStyle(
                color: Colors.grey[600],
                fontSize: 13,
              ),
            ),
            const SizedBox(height: 16),
            
            if (existingBusinesses.isEmpty)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF10B981).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.celebration, color: Color(0xFF10B981)),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'No existing ${widget.businessType.toLowerCase()}s found! Great opportunity.',
                        style: const TextStyle(
                          color: Color(0xFF10B981),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              )
            else
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: existingBusinesses.map((business) {
                  final isCompetitor = 
                      (widget.businessType.toLowerCase() == 'gym' && business['name'] == 'Gyms') ||
                      (widget.businessType.toLowerCase() == 'cafe' && business['name'] == 'Cafes');
                  
                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: isCompetitor 
                          ? const Color(0xFFF59E0B).withOpacity(0.15)
                          : (business['color'] as Color).withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                      border: isCompetitor 
                          ? Border.all(color: const Color(0xFFF59E0B), width: 1.5)
                          : null,
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          business['icon'] as IconData,
                          size: 18,
                          color: isCompetitor 
                              ? const Color(0xFFF59E0B)
                              : business['color'] as Color,
                        ),
                        const SizedBox(width: 6),
                        Text(
                          '${business['count']} ${business['name']}',
                          style: TextStyle(
                            fontWeight: FontWeight.w500,
                            color: isCompetitor 
                                ? const Color(0xFFF59E0B)
                                : Colors.grey[800],
                            fontSize: 13,
                          ),
                        ),
                        if (isCompetitor) ...[
                          const SizedBox(width: 4),
                          const Icon(Icons.warning_rounded, size: 14, color: Color(0xFFF59E0B)),
                        ],
                      ],
                    ),
                  );
                }).toList(),
              ),

            // Show average rating if available
            if (bev.avgRating > 0) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.star, color: Color(0xFFFBBF24), size: 20),
                    const SizedBox(width: 8),
                    Text(
                      'Average Area Rating: ${bev.avgRating.toStringAsFixed(1)}/5.0',
                      style: TextStyle(
                        color: Colors.grey[700],
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildMainCard(EnhancedRecommendation rec, CategoryScore selectedScore, bool isGoodChoice) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: isGoodChoice 
              ? [const Color(0xFF10B981), const Color(0xFF059669)]
              : [const Color(0xFFF59E0B), const Color(0xFFD97706)],
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: (isGoodChoice ? const Color(0xFF10B981) : const Color(0xFFF59E0B)).withOpacity(0.4),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            // Icon and title
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    widget.businessType == 'Gym' ? Icons.fitness_center : Icons.coffee,
                    size: 40,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            // Verdict
            Text(
              isGoodChoice ? '✓ Great Location!' : '⚠ Consider Alternative',
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              isGoodChoice 
                  ? 'This area is ideal for a ${widget.businessType}'
                  : 'A ${rec.recommendation.bestCategory} might perform better here',
              style: TextStyle(
                fontSize: 16,
                color: Colors.white.withOpacity(0.9),
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            
            // Score
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(30),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'Score: ',
                    style: TextStyle(
                      fontSize: 18,
                      color: Colors.grey[600],
                    ),
                  ),
                  Text(
                    '${(selectedScore.score * 100).toInt()}%',
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: isGoodChoice ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
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

  Widget _buildScoreBreakdownCard(CategoryScore score) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.analytics, color: _primaryBlue),
                const SizedBox(width: 8),
                const Text(
                  'Score Breakdown',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            _buildScoreBar('Overall Score', score.score, _primaryBlue),
            if (score.positiveFactors.isNotEmpty) ...[  
              const SizedBox(height: 16),
              const Text(
                'Positive Factors',
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
              ),
              const SizedBox(height: 8),
              ...score.positiveFactors.map((factor) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  children: [
                    const Icon(Icons.check_circle, color: Color(0xFF10B981), size: 16),
                    const SizedBox(width: 8),
                    Expanded(child: Text(factor, style: TextStyle(color: Colors.grey[700], fontSize: 13))),
                  ],
                ),
              )),
            ],
            if (score.concerns.isNotEmpty) ...[  
              const SizedBox(height: 16),
              const Text(
                'Concerns',
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
              ),
              const SizedBox(height: 8),
              ...score.concerns.map((concern) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  children: [
                    const Icon(Icons.warning, color: Color(0xFFF59E0B), size: 16),
                    const SizedBox(width: 8),
                    Expanded(child: Text(concern, style: TextStyle(color: Colors.grey[700], fontSize: 13))),
                  ],
                ),
              )),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildScoreBar(String label, double value, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: TextStyle(color: Colors.grey[600])),
            Text(
              '${(value * 100).toInt()}%',
              style: TextStyle(fontWeight: FontWeight.bold, color: color),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Container(
          height: 8,
          decoration: BoxDecoration(
            color: Colors.grey[200],
            borderRadius: BorderRadius.circular(4),
          ),
          child: FractionallySizedBox(
            alignment: Alignment.centerLeft,
            widthFactor: value,
            child: Container(
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildAlternativeCard(EnhancedRecommendation rec) {
    final alternativeScore = rec.recommendation.bestCategory.toLowerCase() == 'gym' 
        ? rec.gym 
        : rec.cafe;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF10B981), width: 2),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.lightbulb, color: Color(0xFF10B981)),
                const SizedBox(width: 8),
                const Text(
                  'Better Alternative',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF10B981),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Icon(
                  rec.recommendation.bestCategory == 'gym' 
                      ? Icons.fitness_center 
                      : Icons.coffee,
                  size: 32,
                  color: const Color(0xFF10B981),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Consider a ${rec.recommendation.bestCategory.toUpperCase()} instead',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Text(
                        'Score: ${(alternativeScore.score * 100).toInt()}%',
                        style: TextStyle(color: Colors.grey[600]),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFactorsCard(CategoryScore score) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.checklist, color: _primaryBlue),
                const SizedBox(width: 8),
                const Text(
                  'Key Factors',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (score.rulesTriggered != null && score.rulesTriggered!.isNotEmpty)
              ...score.rulesTriggered!.map((rule) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: rule.isPositive ? const Color(0xFF10B981).withOpacity(0.2) : const Color(0xFFF59E0B).withOpacity(0.2),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        rule.delta,
                        style: TextStyle(
                          color: rule.isPositive ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            rule.rule,
                            style: TextStyle(
                              color: Colors.grey[800],
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          if (rule.reason != null)
                            Text(
                              rule.reason!,
                              style: TextStyle(
                                color: Colors.grey[600],
                                fontSize: 12,
                              ),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              ))
            else
              Text(
                'No specific rules triggered',
                style: TextStyle(color: Colors.grey[500]),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildInsightsCard(LLMInsights insights) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [_primaryBlue, _darkBlue],
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: _primaryBlue.withOpacity(0.3),
            blurRadius: 15,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.psychology, color: Colors.white),
                const SizedBox(width: 8),
                const Text(
                  'AI Insights',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text(
                    'Powered by AI',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            // Recommendation
            Text(
              insights.recommendation,
              style: TextStyle(
                color: Colors.white.withOpacity(0.95),
                fontSize: 15,
                height: 1.5,
              ),
            ),
            
            if (insights.keyFactors.isNotEmpty) ...[
              const SizedBox(height: 20),
              const Text(
                '💡 Key Factors',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                  fontSize: 15,
                ),
              ),
              const SizedBox(height: 8),
              ...insights.keyFactors.map((opp) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('• ', style: TextStyle(color: _accentBlue, fontSize: 16)),
                    Expanded(
                      child: Text(
                        opp,
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.9),
                          fontSize: 14,
                        ),
                      ),
                    ),
                  ],
                ),
              )),
            ],
            
            if (insights.risks.isNotEmpty) ...[
              const SizedBox(height: 16),
              const Text(
                '⚠️ Risks to Consider',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                  fontSize: 15,
                ),
              ),
              const SizedBox(height: 8),
              ...insights.risks.map((risk) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('• ', style: TextStyle(color: Colors.orange, fontSize: 16)),
                    Expanded(
                      child: Text(
                        risk,
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.9),
                          fontSize: 14,
                        ),
                      ),
                    ),
                  ],
                ),
              )),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildProcessingInfo(EnhancedRecommendation rec) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            rec.isLLMPowered ? Icons.psychology : Icons.bolt,
            size: 18,
            color: Colors.white.withOpacity(0.7),
          ),
          const SizedBox(width: 8),
          Text(
            '${rec.mode.toUpperCase()} mode • ${rec.processingTimeMs.toStringAsFixed(0)}ms',
            style: TextStyle(
              color: Colors.white.withOpacity(0.7),
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }
}
