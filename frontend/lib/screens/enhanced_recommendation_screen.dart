import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'analysis_results_screen.dart';

class EnhancedRecommendationScreen extends ConsumerStatefulWidget {
  const EnhancedRecommendationScreen({super.key});

  @override
  ConsumerState<EnhancedRecommendationScreen> createState() =>
      _EnhancedRecommendationScreenState();
}

class _EnhancedRecommendationScreenState
    extends ConsumerState<EnhancedRecommendationScreen> {
  // Clifton, Karachi as default center
  static const LatLng _cliftonCenter = LatLng(24.8093, 67.0311);
  
  // Available business types
  static const List<String> _availableBusinessTypes = ['Gym', 'Cafe'];
  
  LatLng _selectedLocation = _cliftonCenter;
  double _selectedRadius = 500.0;
  bool _useAIMode = true;
  String? _selectedBusinessType;
  
  // Search controller
  final TextEditingController _searchController = TextEditingController();
  final FocusNode _searchFocusNode = FocusNode();
  List<String> _filteredBusinessTypes = [];
  bool _showSuggestions = false;
  
  GoogleMapController? _mapController;
  final Completer<GoogleMapController> _controllerCompleter = Completer();

  // Radius options
  final List<double> _radiusOptions = [300, 500, 750, 1000];

  @override
  void initState() {
    super.initState();
    _filteredBusinessTypes = _availableBusinessTypes;
    _searchController.addListener(_onSearchChanged);
    _searchFocusNode.addListener(_onFocusChanged);
  }

  @override
  void dispose() {
    _searchController.removeListener(_onSearchChanged);
    _searchController.dispose();
    _searchFocusNode.removeListener(_onFocusChanged);
    _searchFocusNode.dispose();
    super.dispose();
  }

  void _onSearchChanged() {
    final query = _searchController.text.toLowerCase();
    setState(() {
      if (query.isEmpty) {
        _filteredBusinessTypes = _availableBusinessTypes;
      } else {
        _filteredBusinessTypes = _availableBusinessTypes
            .where((type) => type.toLowerCase().contains(query))
            .toList();
      }
    });
  }

  void _onFocusChanged() {
    if (_searchFocusNode.hasFocus) {
      setState(() {
        _showSuggestions = true;
        _filteredBusinessTypes = _availableBusinessTypes;
      });
    }
  }

  void _selectBusinessType(String type) {
    setState(() {
      _selectedBusinessType = type;
      _searchController.text = type;
      _showSuggestions = false;
      _filteredBusinessTypes = [];
    });
    FocusScope.of(context).unfocus();
  }

  void _showSnackBar(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          behavior: SnackBarBehavior.floating,
          backgroundColor: const Color(0xFF1E40AF),
        ),
      );
    }
  }

  void _onMapTap(LatLng position) {
    // Allow user to select any location on the map
    // Default is Clifton, but user can move anywhere
    setState(() {
      _selectedLocation = position;
    });
  }

  void _onAnalyzePressed() {
    if (_selectedBusinessType == null) {
      _showSnackBar('Please select a business type first');
      return;
    }

    Navigator.push(
      context,
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) => AnalysisResultsScreen(
          latitude: _selectedLocation.latitude,
          longitude: _selectedLocation.longitude,
          radius: _selectedRadius.toInt(),
          isLLMMode: _useAIMode,
          businessType: _selectedBusinessType!,
        ),
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          return FadeTransition(
            opacity: animation,
            child: SlideTransition(
              position: Tween<Offset>(
                begin: const Offset(0, 0.1),
                end: Offset.zero,
              ).animate(CurvedAnimation(
                parent: animation,
                curve: Curves.easeOutCubic,
              )),
              child: child,
            ),
          );
        },
        transitionDuration: const Duration(milliseconds: 400),
      ),
    );
  }

  void _goToClifton() {
    setState(() {
      _selectedLocation = _cliftonCenter;
    });
    _mapController?.animateCamera(
      CameraUpdate.newLatLngZoom(_cliftonCenter, 15),
    );
  }

  Set<Marker> _buildMarkers() {
    return {
      Marker(
        markerId: const MarkerId('selected_location'),
        position: _selectedLocation,
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueAzure),
        infoWindow: InfoWindow(
          title: 'Selected Location',
          snippet: '${_selectedLocation.latitude.toStringAsFixed(4)}, ${_selectedLocation.longitude.toStringAsFixed(4)}',
        ),
      ),
    };
  }

  Set<Circle> _buildCircles() {
    return {
      Circle(
        circleId: const CircleId('analysis_radius'),
        center: _selectedLocation,
        radius: _selectedRadius,
        fillColor: const Color(0xFF1E40AF).withOpacity(0.15),
        strokeColor: const Color(0xFF1E40AF),
        strokeWidth: 2,
      ),
    };
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: GestureDetector(
        onTap: () {
          // Close suggestions dropdown when tapping outside
          if (_showSuggestions) {
            setState(() {
              _showSuggestions = false;
            });
            FocusScope.of(context).unfocus();
          }
        },
        child: Stack(
        children: [
          // Full-screen Google Map
          GoogleMap(
            initialCameraPosition: CameraPosition(
              target: _cliftonCenter,
              zoom: 15,
            ),
            onMapCreated: (GoogleMapController controller) {
              _mapController = controller;
              if (!_controllerCompleter.isCompleted) {
                _controllerCompleter.complete(controller);
              }
            },
            onTap: (position) {
              // Close suggestions if open
              if (_showSuggestions) {
                setState(() {
                  _showSuggestions = false;
                });
              }
              _onMapTap(position);
            },
            markers: _buildMarkers(),
            circles: _buildCircles(),
            myLocationEnabled: false,
            myLocationButtonEnabled: false,
            zoomControlsEnabled: false,
            mapToolbarEnabled: false,
          ),
          
          // Top bar with back button, title and search
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: EdgeInsets.only(
                top: MediaQuery.of(context).padding.top + 8,
                left: 8,
                right: 16,
                bottom: 12,
              ),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    const Color(0xFF1E40AF).withOpacity(0.95),
                    const Color(0xFF1E40AF).withOpacity(0.8),
                    Colors.transparent,
                  ],
                  stops: const [0.0, 0.7, 1.0],
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      IconButton(
                        icon: const Icon(Icons.arrow_back, color: Colors.white),
                        onPressed: () => Navigator.pop(context),
                      ),
                      const SizedBox(width: 8),
                      const Expanded(
                        child: Text(
                          'Location Intelligence',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      // Clifton button
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(8),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.2),
                              blurRadius: 4,
                              offset: const Offset(0, 2),
                            ),
                          ],
                        ),
                        child: IconButton(
                          icon: const Icon(Icons.location_city, color: Color(0xFF1E40AF)),
                          onPressed: _goToClifton,
                          tooltip: 'Go to Clifton',
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  // Business type search bar
                  _buildSearchBar(),
                ],
              ),
            ),
          ),
          
          // Suggestions dropdown
          if (_showSuggestions && _filteredBusinessTypes.isNotEmpty)
            Positioned(
              top: MediaQuery.of(context).padding.top + 120,
              left: 16,
              right: 16,
              child: Material(
                elevation: 8,
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: _filteredBusinessTypes.map((type) {
                      return ListTile(
                        leading: Icon(
                          type == 'Gym' ? Icons.fitness_center : Icons.coffee,
                          color: const Color(0xFF1E40AF),
                        ),
                        title: Text(
                          type,
                          style: const TextStyle(fontWeight: FontWeight.w500),
                        ),
                        subtitle: Text(
                          type == 'Gym' 
                              ? 'Fitness centers & gyms' 
                              : 'Coffee shops & cafes',
                          style: TextStyle(color: Colors.grey[600], fontSize: 12),
                        ),
                        onTap: () => _selectBusinessType(type),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
            ),
          
          // Bottom compact control bar
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: EdgeInsets.only(
                left: 16,
                right: 16,
                top: 16,
                bottom: MediaQuery.of(context).padding.bottom + 16,
              ),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF1E40AF).withOpacity(0.15),
                    blurRadius: 20,
                    offset: const Offset(0, -5),
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Handle indicator
                  Container(
                    width: 40,
                    height: 4,
                    margin: const EdgeInsets.only(bottom: 16),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1E40AF).withOpacity(0.3),
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  
                  // Selected business type display
                  if (_selectedBusinessType != null) ...[
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E40AF).withOpacity(0.08),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: const Color(0xFF1E40AF).withOpacity(0.2),
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            _selectedBusinessType == 'Gym' 
                                ? Icons.fitness_center 
                                : Icons.coffee,
                            color: const Color(0xFF1E40AF),
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            'Analyzing for: $_selectedBusinessType',
                            style: const TextStyle(
                              color: Color(0xFF1E40AF),
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const Spacer(),
                          GestureDetector(
                            onTap: () {
                              setState(() {
                                _selectedBusinessType = null;
                                _searchController.clear();
                              });
                            },
                            child: const Icon(
                              Icons.close,
                              color: Color(0xFF1E40AF),
                              size: 18,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                  ],
                  
                  // Mode toggle and radius in one row
                  Row(
                    children: [
                      // Mode toggle
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: const Color(0xFF1E40AF).withOpacity(0.08),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Row(
                            children: [
                              Expanded(
                                child: GestureDetector(
                                  onTap: () => setState(() => _useAIMode = false),
                                  child: AnimatedContainer(
                                    duration: const Duration(milliseconds: 200),
                                    padding: const EdgeInsets.symmetric(vertical: 10),
                                    decoration: BoxDecoration(
                                      color: !_useAIMode ? const Color(0xFF1E40AF) : Colors.transparent,
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Row(
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: [
                                        Icon(
                                          Icons.speed,
                                          size: 16,
                                          color: !_useAIMode ? Colors.white : const Color(0xFF1E40AF),
                                        ),
                                        const SizedBox(width: 4),
                                        Text(
                                          'Fast',
                                          style: TextStyle(
                                            color: !_useAIMode ? Colors.white : const Color(0xFF1E40AF),
                                            fontWeight: FontWeight.w600,
                                            fontSize: 13,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                              Expanded(
                                child: GestureDetector(
                                  onTap: () => setState(() => _useAIMode = true),
                                  child: AnimatedContainer(
                                    duration: const Duration(milliseconds: 200),
                                    padding: const EdgeInsets.symmetric(vertical: 10),
                                    decoration: BoxDecoration(
                                      color: _useAIMode ? const Color(0xFF1E40AF) : Colors.transparent,
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Row(
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: [
                                        Icon(
                                          Icons.auto_awesome,
                                          size: 16,
                                          color: _useAIMode ? Colors.white : const Color(0xFF1E40AF),
                                        ),
                                        const SizedBox(width: 4),
                                        Text(
                                          'AI',
                                          style: TextStyle(
                                            color: _useAIMode ? Colors.white : const Color(0xFF1E40AF),
                                            fontWeight: FontWeight.w600,
                                            fontSize: 13,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      
                      const SizedBox(width: 12),
                      
                      // Radius dropdown
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1E40AF).withOpacity(0.08),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<double>(
                            value: _selectedRadius,
                            icon: const Icon(Icons.keyboard_arrow_down, size: 20, color: Color(0xFF1E40AF)),
                            isDense: true,
                            items: _radiusOptions.map((radius) {
                              return DropdownMenuItem(
                                value: radius,
                                child: Text(
                                  '${radius.toInt()}m',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w600,
                                    fontSize: 13,
                                    color: Color(0xFF1E40AF),
                                  ),
                                ),
                              );
                            }).toList(),
                            onChanged: (value) {
                              if (value != null) {
                                setState(() => _selectedRadius = value);
                              }
                            },
                          ),
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // Analyze button - full width
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _selectedBusinessType != null ? _onAnalyzePressed : null,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF1E40AF),
                        foregroundColor: Colors.white,
                        disabledBackgroundColor: Colors.grey[300],
                        disabledForegroundColor: Colors.grey[500],
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        elevation: _selectedBusinessType != null ? 4 : 0,
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            _useAIMode ? Icons.auto_awesome : Icons.analytics,
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            _selectedBusinessType != null
                                ? (_useAIMode ? 'Analyze with AI' : 'Quick Analysis')
                                : 'Select a business type first',
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
      ),
    );
  }

  Widget _buildSearchBar() {
    return GestureDetector(
      onTap: () {
        _searchFocusNode.requestFocus();
        setState(() {
          _showSuggestions = true;
          _filteredBusinessTypes = _availableBusinessTypes;
        });
      },
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: TextField(
          controller: _searchController,
          focusNode: _searchFocusNode,
          onTap: () {
            setState(() {
              _showSuggestions = true;
              _filteredBusinessTypes = _availableBusinessTypes;
            });
          },
          decoration: InputDecoration(
            hintText: _selectedBusinessType ?? 'Tap to select business type...',
            hintStyle: TextStyle(
              color: _selectedBusinessType != null ? Colors.black87 : Colors.grey[400],
              fontWeight: _selectedBusinessType != null ? FontWeight.w500 : FontWeight.normal,
            ),
            prefixIcon: Icon(
              _selectedBusinessType == 'Gym' 
                  ? Icons.fitness_center 
                  : _selectedBusinessType == 'Cafe' 
                      ? Icons.coffee 
                      : Icons.search,
              color: const Color(0xFF1E40AF),
            ),
            suffixIcon: _selectedBusinessType != null
                ? IconButton(
                    icon: const Icon(Icons.clear, color: Colors.grey),
                    onPressed: () {
                      _searchController.clear();
                      setState(() {
                        _selectedBusinessType = null;
                        _showSuggestions = false;
                      });
                    },
                  )
                : const Icon(Icons.arrow_drop_down, color: Color(0xFF1E40AF)),
            border: InputBorder.none,
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          ),
          style: const TextStyle(fontSize: 16),
          readOnly: true, // Make it read-only so it acts like a dropdown
        ),
      ),
    );
  }
}
