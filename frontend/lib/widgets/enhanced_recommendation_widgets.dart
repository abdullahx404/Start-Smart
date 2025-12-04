import 'package:flutter/material.dart';
import '../models/enhanced_recommendation.dart';
import '../utils/colors.dart';

/// Suitability badge widget showing the recommendation level
class SuitabilityBadge extends StatelessWidget {
  final String suitability;
  final double? score;
  final bool showScore;
  final bool large;

  const SuitabilityBadge({
    super.key,
    required this.suitability,
    this.score,
    this.showScore = true,
    this.large = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: large ? 16 : 12,
        vertical: large ? 8 : 6,
      ),
      decoration: BoxDecoration(
        color: _getBackgroundColor(),
        borderRadius: BorderRadius.circular(large ? 12 : 8),
        border: Border.all(color: _getBorderColor(), width: 1.5),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(_getEmoji(), style: TextStyle(fontSize: large ? 20 : 16)),
          const SizedBox(width: 6),
          Text(
            _getLabel(),
            style: TextStyle(
              color: _getTextColor(),
              fontWeight: FontWeight.w600,
              fontSize: large ? 16 : 14,
            ),
          ),
          if (showScore && score != null) ...[
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.3),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                '${(score! * 100).round()}%',
                style: TextStyle(
                  color: _getTextColor(),
                  fontWeight: FontWeight.bold,
                  fontSize: large ? 14 : 12,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _getEmoji() {
    switch (suitability) {
      case 'excellent':
        return '🌟';
      case 'good':
        return '✅';
      case 'moderate':
        return '⚠️';
      case 'poor':
        return '❌';
      case 'not_recommended':
        return '🚫';
      default:
        return '❓';
    }
  }

  String _getLabel() {
    switch (suitability) {
      case 'excellent':
        return 'Excellent';
      case 'good':
        return 'Good';
      case 'moderate':
        return 'Moderate';
      case 'poor':
        return 'Poor';
      case 'not_recommended':
        return 'Not Recommended';
      default:
        return suitability;
    }
  }

  Color _getBackgroundColor() {
    switch (suitability) {
      case 'excellent':
        return const Color(0xFF1B5E20).withValues(alpha: 0.15);
      case 'good':
        return const Color(0xFF388E3C).withValues(alpha: 0.15);
      case 'moderate':
        return const Color(0xFFF57C00).withValues(alpha: 0.15);
      case 'poor':
        return const Color(0xFFD32F2F).withValues(alpha: 0.15);
      case 'not_recommended':
        return const Color(0xFF424242).withValues(alpha: 0.15);
      default:
        return Colors.grey.withValues(alpha: 0.15);
    }
  }

  Color _getBorderColor() {
    switch (suitability) {
      case 'excellent':
        return const Color(0xFF1B5E20);
      case 'good':
        return const Color(0xFF388E3C);
      case 'moderate':
        return const Color(0xFFF57C00);
      case 'poor':
        return const Color(0xFFD32F2F);
      case 'not_recommended':
        return const Color(0xFF424242);
      default:
        return Colors.grey;
    }
  }

  Color _getTextColor() {
    switch (suitability) {
      case 'excellent':
        return const Color(0xFF1B5E20);
      case 'good':
        return const Color(0xFF2E7D32);
      case 'moderate':
        return const Color(0xFFE65100);
      case 'poor':
        return const Color(0xFFC62828);
      case 'not_recommended':
        return const Color(0xFF424242);
      default:
        return Colors.grey;
    }
  }
}

/// Card showing category score with reasoning
class CategoryScoreCard extends StatelessWidget {
  final String category;
  final CategoryScore score;
  final bool isWinner;
  final VoidCallback? onTap;

  const CategoryScoreCard({
    super.key,
    required this.category,
    required this.score,
    this.isWinner = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final icon = category.toLowerCase() == 'gym' ? '🏋️' : '☕';

    return Card(
      elevation: isWinner ? 4 : 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: isWinner
            ? BorderSide(color: AppColors.primary, width: 2)
            : BorderSide.none,
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header row
              Row(
                children: [
                  Text(icon, style: const TextStyle(fontSize: 28)),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              category,
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            if (isWinner) ...[
                              const SizedBox(width: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 2,
                                ),
                                decoration: BoxDecoration(
                                  color: AppColors.primary,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: const Text(
                                  'BEST',
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
                        SuitabilityBadge(
                          suitability: score.suitability,
                          score: score.score,
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              // Reasoning (if available)
              if (score.reasoning != null && score.reasoning!.isNotEmpty) ...[
                const SizedBox(height: 16),
                const Divider(),
                const SizedBox(height: 12),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(
                      Icons.lightbulb_outline,
                      size: 18,
                      color: Colors.amber,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        score.reasoning!,
                        style: TextStyle(
                          color: Colors.grey[700],
                          fontSize: 14,
                          height: 1.4,
                        ),
                      ),
                    ),
                  ],
                ),
              ],

              // Positive factors
              if (score.positiveFactors.isNotEmpty) ...[
                const SizedBox(height: 16),
                _buildFactorsList(
                  'Advantages',
                  score.positiveFactors,
                  Icons.thumb_up,
                  AppColors.success,
                ),
              ],

              // Concerns
              if (score.concerns.isNotEmpty) ...[
                const SizedBox(height: 12),
                _buildFactorsList(
                  'Concerns',
                  score.concerns,
                  Icons.warning_amber,
                  AppColors.warning,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFactorsList(
    String title,
    List<String> factors,
    IconData icon,
    Color color,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 16, color: color),
            const SizedBox(width: 6),
            Text(
              title,
              style: TextStyle(
                fontWeight: FontWeight.w600,
                color: color,
                fontSize: 13,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ...factors.map(
          (factor) => Padding(
            padding: const EdgeInsets.only(left: 22, bottom: 4),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('• ', style: TextStyle(color: color)),
                Expanded(
                  child: Text(
                    factor,
                    style: TextStyle(fontSize: 13, color: Colors.grey[700]),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

/// Card showing LLM insights (key factors, risks, recommendation)
class LLMInsightsCard extends StatelessWidget {
  final LLMInsights insights;

  const LLMInsightsCard({super.key, required this.insights});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.purple.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.psychology,
                    color: Colors.purple,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'AI Analysis',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      'Powered by LLM',
                      style: TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                  ],
                ),
              ],
            ),

            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 12),

            // Recommendation summary
            if (insights.recommendation.isNotEmpty) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.blue.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.blue.withValues(alpha: 0.3)),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(
                      Icons.tips_and_updates,
                      color: Colors.blue,
                      size: 20,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        insights.recommendation,
                        style: const TextStyle(fontSize: 14, height: 1.5),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Key factors
            if (insights.keyFactors.isNotEmpty) ...[
              _buildSection(
                'Key Factors',
                insights.keyFactors,
                Icons.key,
                Colors.green,
              ),
              const SizedBox(height: 12),
            ],

            // Risks
            if (insights.risks.isNotEmpty) ...[
              _buildSection(
                'Potential Risks',
                insights.risks,
                Icons.warning_amber,
                Colors.orange,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSection(
    String title,
    List<String> items,
    IconData icon,
    Color color,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 18, color: color),
            const SizedBox(width: 8),
            Text(
              title,
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 14,
                color: color,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ...items.map(
          (item) => Padding(
            padding: const EdgeInsets.only(left: 26, bottom: 6),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  margin: const EdgeInsets.only(top: 6),
                  width: 6,
                  height: 6,
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.6),
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    item,
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.grey[700],
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

/// Score comparison widget showing gym vs cafe
class ScoreComparison extends StatelessWidget {
  final double gymScore;
  final double cafeScore;
  final String? winner;

  const ScoreComparison({
    super.key,
    required this.gymScore,
    required this.cafeScore,
    this.winner,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: _buildScoreBar(
                  '🏋️ Gym',
                  gymScore,
                  winner?.toLowerCase() == 'gym',
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildScoreBar(
                  '☕ Cafe',
                  cafeScore,
                  winner?.toLowerCase() == 'cafe',
                ),
              ),
            ],
          ),
          if (winner != null) ...[
            const SizedBox(height: 12),
            Text(
              winner!.toLowerCase() == 'gym'
                  ? 'Gym is ${((gymScore - cafeScore) * 100).abs().round()}% better suited'
                  : 'Cafe is ${((cafeScore - gymScore) * 100).abs().round()}% better suited',
              style: TextStyle(color: Colors.grey[600], fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildScoreBar(String label, double score, bool isWinner) {
    final color = isWinner ? AppColors.primary : Colors.grey;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: TextStyle(
                fontWeight: isWinner ? FontWeight.bold : FontWeight.normal,
                color: isWinner ? AppColors.primary : Colors.grey[700],
              ),
            ),
            Text(
              '${(score * 100).round()}%',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: isWinner ? AppColors.primary : Colors.grey[700],
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        LinearProgressIndicator(
          value: score,
          backgroundColor: Colors.grey[300],
          valueColor: AlwaysStoppedAnimation<Color>(color),
          minHeight: 8,
          borderRadius: BorderRadius.circular(4),
        ),
      ],
    );
  }
}

/// Mode toggle for Fast vs LLM recommendations
class RecommendationModeToggle extends StatelessWidget {
  final bool isLLMMode;
  final ValueChanged<bool> onChanged;
  final bool isLoading;

  const RecommendationModeToggle({
    super.key,
    required this.isLLMMode,
    required this.onChanged,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Colors.grey[200],
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _buildToggleButton(
            label: 'Fast',
            icon: Icons.bolt,
            isSelected: !isLLMMode,
            onTap: isLoading ? null : () => onChanged(false),
          ),
          _buildToggleButton(
            label: 'AI Powered',
            icon: Icons.psychology,
            isSelected: isLLMMode,
            onTap: isLoading ? null : () => onChanged(true),
          ),
        ],
      ),
    );
  }

  Widget _buildToggleButton({
    required String label,
    required IconData icon,
    required bool isSelected,
    VoidCallback? onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 18,
              color: isSelected ? Colors.white : Colors.grey[600],
            ),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? Colors.white : Colors.grey[600],
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Processing indicator for API calls
class ProcessingIndicator extends StatelessWidget {
  final String message;
  final int? processingTimeMs;

  const ProcessingIndicator({
    super.key,
    this.message = 'Analyzing location...',
    this.processingTimeMs,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const CircularProgressIndicator(),
        const SizedBox(height: 16),
        Text(message, style: TextStyle(color: Colors.grey[600], fontSize: 14)),
        if (processingTimeMs != null) ...[
          const SizedBox(height: 8),
          Text(
            'Processed in ${processingTimeMs}ms',
            style: TextStyle(color: Colors.grey[500], fontSize: 12),
          ),
        ],
      ],
    );
  }
}
