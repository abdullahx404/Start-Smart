import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/selection_provider.dart';
import '../utils/colors.dart';
import '../utils/constants.dart';
import 'map_screen.dart';

/// Landing screen - Entry point for the app
class LandingScreen extends ConsumerStatefulWidget {
  const LandingScreen({super.key});

  @override
  ConsumerState<LandingScreen> createState() => _LandingScreenState();
}

class _LandingScreenState extends ConsumerState<LandingScreen> {
  String? _selectedNeighborhood;
  String _selectedCategory = Categories.gym;

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
            const Text(
              'What type of business?',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 12),

            // Category selection
            Row(
              children: Categories.all.map((category) {
                final isSelected = category == _selectedCategory;
                return Expanded(
                  child: Padding(
                    padding: EdgeInsets.only(
                      right: category != Categories.all.last ? 12 : 0,
                    ),
                    child: _CategoryCard(
                      category: category,
                      isSelected: isSelected,
                      onTap: () {
                        setState(() {
                          _selectedCategory = category;
                        });
                      },
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 24),

            const Text(
              'Which neighborhood?',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 12),

            // Neighborhood dropdown
            Container(
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.surfaceVariant),
                borderRadius: BorderRadius.circular(8),
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: _selectedNeighborhood,
                  hint: const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16),
                    child: Text('Select a neighborhood'),
                  ),
                  isExpanded: true,
                  icon: const Padding(
                    padding: EdgeInsets.only(right: 12),
                    child: Icon(Icons.arrow_drop_down),
                  ),
                  items: Neighborhoods.all.entries.map((entry) {
                    return DropdownMenuItem(
                      value: entry.key,
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        child: Row(
                          children: [
                            const Text('📍', style: TextStyle(fontSize: 16)),
                            const SizedBox(width: 8),
                            Text(entry.value),
                          ],
                        ),
                      ),
                    );
                  }).toList(),
                  onChanged: (value) {
                    setState(() {
                      _selectedNeighborhood = value;
                    });
                  },
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFindButton() {
    final isEnabled = _selectedNeighborhood != null;

    return ElevatedButton(
      onPressed: isEnabled
          ? () {
              // Update providers
              ref.read(selectedCategoryProvider.notifier).state =
                  _selectedCategory;
              ref.read(selectedNeighborhoodProvider.notifier).state =
                  _selectedNeighborhood;

              // Navigate to map screen
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const MapScreen()),
              );
            }
          : null,
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.surface,
        foregroundColor: AppColors.primary,
        disabledBackgroundColor: AppColors.surface.withValues(alpha: 0.5),
        disabledForegroundColor: AppColors.textHint,
        padding: const EdgeInsets.symmetric(vertical: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        elevation: isEnabled ? 4 : 0,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.search,
            color: isEnabled ? AppColors.primary : AppColors.textHint,
          ),
          const SizedBox(width: 8),
          Text(
            'Find Locations',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: isEnabled ? AppColors.primary : AppColors.textHint,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeaturesSection() {
    return Column(
      children: [
        _buildFeatureItem(
          icon: Icons.analytics,
          title: 'Data-Driven Insights',
          description: 'Powered by real business data and social signals',
        ),
        const SizedBox(height: 16),
        _buildFeatureItem(
          icon: Icons.map,
          title: 'Interactive Heatmaps',
          description: 'Visualize opportunities across neighborhoods',
        ),
        const SizedBox(height: 16),
        _buildFeatureItem(
          icon: Icons.lightbulb,
          title: 'Smart Recommendations',
          description: 'Get top locations with explainable rationale',
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

/// Category selection card
class _CategoryCard extends StatelessWidget {
  final String category;
  final bool isSelected;
  final VoidCallback onTap;

  const _CategoryCard({
    required this.category,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: isSelected
              ? AppColors.primary.withValues(alpha: 0.1)
              : AppColors.surfaceVariant.withValues(alpha: 0.5),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isSelected ? AppColors.primary : Colors.transparent,
            width: 2,
          ),
        ),
        child: Column(
          children: [
            Text(
              Categories.getIcon(category),
              style: const TextStyle(fontSize: 32),
            ),
            const SizedBox(height: 8),
            Text(
              category,
              style: TextStyle(
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                color: isSelected ? AppColors.primary : AppColors.textPrimary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
