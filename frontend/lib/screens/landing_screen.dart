import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../utils/colors.dart';
import 'enhanced_recommendation_screen.dart';

/// Landing screen - Entry point for the app
class LandingScreen extends ConsumerStatefulWidget {
  const LandingScreen({super.key});

  @override
  ConsumerState<LandingScreen> createState() => _LandingScreenState();
}

class _LandingScreenState extends ConsumerState<LandingScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [AppColors.primary, AppColors.primaryDark],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 40),

                // Logo and title
                _buildHeader(),
                const SizedBox(height: 40),

                // Selection card
                _buildSelectionCard(),
                const SizedBox(height: 24),

                // Find locations button
                _buildFindButton(),
                const SizedBox(height: 40),

                // Features section
                _buildFeaturesSection(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Column(
      children: [
        // App icon/logo
        Container(
          width: 100,
          height: 100,
          decoration: BoxDecoration(
            color: AppColors.surface,
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.2),
                blurRadius: 20,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: const Center(
            child: Text('📍', style: TextStyle(fontSize: 48)),
          ),
        ),
        const SizedBox(height: 24),

        // App name
        const Text(
          'StartSmart',
          style: TextStyle(
            fontSize: 36,
            fontWeight: FontWeight.bold,
            color: AppColors.textOnPrimary,
          ),
        ),
        const SizedBox(height: 8),

        // Tagline
        Text(
          'Find the perfect location for your business',
          style: TextStyle(
            fontSize: 16,
            color: AppColors.textOnPrimary.withValues(alpha: 0.9),
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildSelectionCard() {
    return Card(
      elevation: 8,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Info about the AI-powered analysis
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: AppColors.primary.withValues(alpha: 0.2),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.psychology, color: AppColors.primary, size: 28),
                      const SizedBox(width: 12),
                      const Text(
                        'AI-Powered Location Analysis',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Tap on any location in Clifton, Karachi to get intelligent business recommendations for Gym and Cafe.',
                    style: TextStyle(fontSize: 14, color: Colors.black87),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Features list
            _buildInfoRow(Icons.map, 'Select any location on the map'),
            const SizedBox(height: 8),
            _buildInfoRow(Icons.tune, 'Choose analysis radius (300-1000m)'),
            const SizedBox(height: 8),
            _buildInfoRow(Icons.bolt, 'Fast mode: Rule-based (~200ms)'),
            const SizedBox(height: 8),
            _buildInfoRow(Icons.psychology, 'AI mode: LLM insights (~2-3s)'),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String text) {
    return Row(
      children: [
        Icon(icon, size: 20, color: AppColors.primary.withValues(alpha: 0.7)),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(fontSize: 14),
          ),
        ),
      ],
    );
  }

  Widget _buildFindButton() {
    return Column(
      children: [
        // AI-Powered Analysis button (Primary feature)
        ElevatedButton(
          onPressed: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => const EnhancedRecommendationScreen(),
              ),
            );
          },
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.surface,
            foregroundColor: AppColors.primary,
            padding: const EdgeInsets.symmetric(vertical: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            elevation: 4,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.psychology, color: AppColors.primary),
              const SizedBox(width: 8),
              const Text(
                'AI-Powered Analysis',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: AppColors.primary,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildFeaturesSection() {
    return Column(
      children: [
        _buildFeatureItem(
          icon: Icons.psychology,
          title: 'AI-Powered Analysis',
          description: 'LLM-driven insights with detailed reasoning',
        ),
        const SizedBox(height: 16),
        _buildFeatureItem(
          icon: Icons.analytics,
          title: 'Data-Driven Insights',
          description: 'Powered by real Google Places data',
        ),
        const SizedBox(height: 16),
        _buildFeatureItem(
          icon: Icons.map,
          title: '100m Micro-Grids',
          description: 'High-resolution location analysis',
        ),
        const SizedBox(height: 16),
        _buildFeatureItem(
          icon: Icons.lightbulb,
          title: 'Smart Recommendations',
          description: 'Explainable factors and risk analysis',
        ),
      ],
    );
  }

  Widget _buildFeatureItem({
    required IconData icon,
    required String title,
    required String description,
  }) {
    return Row(
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: AppColors.surface.withValues(alpha: 0.2),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: AppColors.textOnPrimary, size: 24),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  color: AppColors.textOnPrimary,
                  fontSize: 15,
                ),
              ),
              Text(
                description,
                style: TextStyle(
                  color: AppColors.textOnPrimary.withValues(alpha: 0.8),
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
