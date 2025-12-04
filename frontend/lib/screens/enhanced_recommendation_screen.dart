import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../models/enhanced_recommendation.dart';
import '../services/api_service.dart';
import '../utils/colors.dart';
import '../utils/constants.dart';
import '../widgets/enhanced_recommendation_widgets.dart';

/// Screen for getting AI-powered location recommendations
class EnhancedRecommendationScreen extends StatefulWidget {
  const EnhancedRecommendationScreen({super.key});

  @override
  State<EnhancedRecommendationScreen> createState() =>
      _EnhancedRecommendationScreenState();
}

class _EnhancedRecommendationScreenState
    extends State<EnhancedRecommendationScreen> {
  final ApiService _apiService = ApiService();
  final MapController _mapController = MapController();
  final TextEditingController _latController = TextEditingController();
  final TextEditingController _lonController = TextEditingController();

  // Default to Clifton, Karachi
  LatLng _selectedLocation = const LatLng(24.8185, 67.0295);
  int _radius = 500;
  bool _isLLMMode = true;
  bool _isLoading = false;
  EnhancedRecommendation? _recommendation;
  String? _error;

  @override
  void initState() {
    super.initState();
    _latController.text = _selectedLocation.latitude.toStringAsFixed(6);
    _lonController.text = _selectedLocation.longitude.toStringAsFixed(6);
  }

  @override
  void dispose() {
    _apiService.dispose();
    _latController.dispose();
    _lonController.dispose();
    super.dispose();
  }

  Future<void> _getRecommendation() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final recommendation = _isLLMMode
          ? await _apiService.getLLMRecommendation(
              lat: _selectedLocation.latitude,
              lon: _selectedLocation.longitude,
              radius: _radius,
            )
          : await _apiService.getFastRecommendation(
              lat: _selectedLocation.latitude,
              lon: _selectedLocation.longitude,
              radius: _radius,
            );

      setState(() {
        _recommendation = recommendation;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _onMapTap(TapPosition tapPosition, LatLng point) {
    setState(() {
      _selectedLocation = point;
      _latController.text = point.latitude.toStringAsFixed(6);
      _lonController.text = point.longitude.toStringAsFixed(6);
      _recommendation = null;
    });
  }

  void _updateLocationFromText() {
    final lat = double.tryParse(_latController.text);
    final lon = double.tryParse(_lonController.text);
    if (lat != null && lon != null) {
      setState(() {
        _selectedLocation = LatLng(lat, lon);
        _recommendation = null;
      });
      _mapController.move(_selectedLocation, _mapController.camera.zoom);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Location Intelligence'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: _showInfoDialog,
          ),
        ],
      ),
      body: Column(
        children: [
          // Map section
          Expanded(flex: 2, child: _buildMap()),

          // Controls section
          Container(
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.1),
                  blurRadius: 10,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [_buildLocationInput(), _buildControls()],
            ),
          ),

          // Results section
          Expanded(flex: 3, child: _buildResults()),
        ],
      ),
    );
  }

  Widget _buildMap() {
    return Stack(
      children: [
        FlutterMap(
          mapController: _mapController,
          options: MapOptions(
            initialCenter: _selectedLocation,
            initialZoom: 15,
            onTap: _onMapTap,
          ),
          children: [
            TileLayer(
              urlTemplate: MapConstants.tileUrlTemplate,
              userAgentPackageName: MapConstants.tileUserAgent,
            ),
            // Radius circle
            CircleLayer(
              circles: [
                CircleMarker(
                  point: _selectedLocation,
                  radius: _radius.toDouble(),
                  useRadiusInMeter: true,
                  color: AppColors.primary.withValues(alpha: 0.15),
                  borderColor: AppColors.primary,
                  borderStrokeWidth: 2,
                ),
              ],
            ),
            // Selected location marker
            MarkerLayer(
              markers: [
                Marker(
                  point: _selectedLocation,
                  width: 50,
                  height: 50,
                  child: const Icon(
                    Icons.location_pin,
                    color: AppColors.primary,
                    size: 50,
                  ),
                ),
              ],
            ),
          ],
        ),
        // Zoom controls
        Positioned(
          right: 16,
          bottom: 16,
          child: Column(
            children: [
              FloatingActionButton.small(
                heroTag: 'zoomIn',
                onPressed: () => _mapController.move(
                  _mapController.camera.center,
                  _mapController.camera.zoom + 1,
                ),
                child: const Icon(Icons.add),
              ),
              const SizedBox(height: 8),
              FloatingActionButton.small(
                heroTag: 'zoomOut',
                onPressed: () => _mapController.move(
                  _mapController.camera.center,
                  _mapController.camera.zoom - 1,
                ),
                child: const Icon(Icons.remove),
              ),
            ],
          ),
        ),
        // Instruction overlay
        Positioned(
          top: 8,
          left: 8,
          right: 8,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.9),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.touch_app, size: 16, color: Colors.grey),
                SizedBox(width: 8),
                Text(
                  'Tap on map to select location',
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildLocationInput() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _latController,
              decoration: const InputDecoration(
                labelText: 'Latitude',
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                isDense: true,
              ),
              keyboardType: TextInputType.number,
              onSubmitted: (_) => _updateLocationFromText(),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: TextField(
              controller: _lonController,
              decoration: const InputDecoration(
                labelText: 'Longitude',
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                isDense: true,
              ),
              keyboardType: TextInputType.number,
              onSubmitted: (_) => _updateLocationFromText(),
            ),
          ),
          const SizedBox(width: 12),
          IconButton(
            onPressed: _updateLocationFromText,
            icon: const Icon(Icons.search),
            style: IconButton.styleFrom(
              backgroundColor: AppColors.primary.withValues(alpha: 0.1),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildControls() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
      child: Row(
        children: [
          // Mode toggle
          Expanded(
            child: RecommendationModeToggle(
              isLLMMode: _isLLMMode,
              onChanged: (value) {
                setState(() {
                  _isLLMMode = value;
                  _recommendation = null;
                });
              },
              isLoading: _isLoading,
            ),
          ),
          const SizedBox(width: 16),
          // Radius selector
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.grey[300]!),
              borderRadius: BorderRadius.circular(8),
            ),
            child: DropdownButton<int>(
              value: _radius,
              underline: const SizedBox(),
              items: [300, 500, 750, 1000].map((r) {
                return DropdownMenuItem(value: r, child: Text('${r}m'));
              }).toList(),
              onChanged: (value) {
                if (value != null) {
                  setState(() {
                    _radius = value;
                    _recommendation = null;
                  });
                }
              },
            ),
          ),
          const SizedBox(width: 16),
          // Analyze button
          ElevatedButton.icon(
            onPressed: _isLoading ? null : _getRecommendation,
            icon: _isLoading
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : const Icon(Icons.analytics),
            label: Text(_isLoading ? 'Analyzing...' : 'Analyze'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResults() {
    if (_isLoading) {
      return Center(
        child: ProcessingIndicator(
          message: _isLLMMode
              ? 'AI is analyzing this location...'
              : 'Quick analysis in progress...',
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: AppColors.error),
            const SizedBox(height: 16),
            Text('Error', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32),
              child: Text(
                _error!,
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey[600]),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _getRecommendation,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_recommendation == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.map_outlined, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              'Select a location and tap Analyze',
              style: TextStyle(color: Colors.grey[600], fontSize: 16),
            ),
            const SizedBox(height: 8),
            Text(
              _isLLMMode
                  ? 'AI-powered analysis takes 2-3 seconds'
                  : 'Fast analysis takes ~200ms',
              style: TextStyle(color: Colors.grey[400], fontSize: 12),
            ),
          ],
        ),
      );
    }

    return _buildRecommendationResults(_recommendation!);
  }

  Widget _buildRecommendationResults(EnhancedRecommendation rec) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Summary card
          Card(
            color: AppColors.primary.withValues(alpha: 0.05),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        rec.recommendation.bestCategory == 'gym' ? '🏋️' : '☕',
                        style: const TextStyle(fontSize: 32),
                      ),
                      const SizedBox(width: 12),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Best for ${rec.recommendation.bestCategory.toUpperCase()}',
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          SuitabilityBadge(
                            suitability: rec.recommendation.suitability,
                            score: rec.recommendation.score,
                            large: true,
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    rec.recommendation.message,
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey[700], fontSize: 14),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        rec.isLLMPowered ? Icons.psychology : Icons.bolt,
                        size: 14,
                        color: Colors.grey,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '${rec.mode.toUpperCase()} mode • ${rec.processingTimeMs}ms',
                        style: TextStyle(color: Colors.grey[500], fontSize: 11),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          // Score comparison
          ScoreComparison(
            gymScore: rec.gym.score,
            cafeScore: rec.cafe.score,
            winner: rec.recommendation.bestCategory,
          ),

          const SizedBox(height: 16),

          // Category cards
          CategoryScoreCard(
            category: 'Gym',
            score: rec.gym,
            isWinner: rec.recommendation.bestCategory == 'gym',
          ),
          const SizedBox(height: 12),
          CategoryScoreCard(
            category: 'Cafe',
            score: rec.cafe,
            isWinner: rec.recommendation.bestCategory == 'cafe',
          ),

          // LLM insights (if available)
          if (rec.llmInsights != null) ...[
            const SizedBox(height: 16),
            LLMInsightsCard(insights: rec.llmInsights!),
          ],

          const SizedBox(height: 24),
        ],
      ),
    );
  }

  void _showInfoDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.info, color: AppColors.primary),
            SizedBox(width: 8),
            Text('About'),
          ],
        ),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'StartSmart Location Intelligence',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 12),
            Text('🚀 Fast Mode: Rule-based analysis (~200ms)'),
            SizedBox(height: 8),
            Text('🧠 AI Mode: LLM-powered insights (2-3s)'),
            SizedBox(height: 16),
            Text(
              'The AI mode uses Groq LLM to provide contextual reasoning '
              'and detailed insights about the location.',
              style: TextStyle(fontSize: 13, color: Colors.grey),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }
}
