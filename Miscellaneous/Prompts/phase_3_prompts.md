# Phase 3: Frontend MVP Interface (Flutter)

**PREREQUISITES**: Phase 2 must be complete with PHASE_LOG.md updated. The backend should have scored grids in the grid_metrics table.

**READ THIS FIRST**: This file contains sequential prompts to implement Phase 3. Feed these to GitHub Copilot **one by one**, in order.

---

## Prompt 1: Read Phase 2 Handoff and Set Up Flutter Project

```
I am implementing Phase 3 of the StartSmart MVP project (Frontend Interface).

First, please read PHASE_LOG.md Phase 2 handoff to understand:
- What scoring data is available
- Which backend functions to call
- Expected API endpoints (even if not yet implemented, we'll use mock data initially)

Then create a new Flutter project:

```powershell
cd frontend
flutter create --org com.startsmart --platforms web,android,ios .
```

Update pubspec.yaml to include necessary dependencies:
- flutter_map: ^6.1.0 (for maps)
- latlong2: ^0.9.0 (coordinates)
- http: ^1.1.0 (API calls)
- flutter_riverpod: ^2.4.0 (state management)
- shared_preferences: ^2.2.2 (local storage)
- intl: ^0.18.1 (date formatting)

Run flutter pub get after updating.

Create the following directory structure under lib/:
lib/
├── main.dart
├── models/
│   ├── grid.dart
│   ├── recommendation.dart
│   ├── grid_detail.dart
├── providers/
│   ├── data_provider.dart
│   ├── selection_provider.dart
├── screens/
│   ├── landing_screen.dart
│   ├── map_screen.dart
│   ├── grid_detail_screen.dart
├── widgets/
│   ├── heatmap_overlay.dart
│   ├── recommendation_card.dart
│   ├── filter_panel.dart
├── services/
│   ├── api_service.dart
│   ├── mock_data_service.dart
├── utils/
    ├── constants.dart
    ├── colors.dart
```

---

## Prompt 2: Create Data Models

```
Create Flutter models matching the backend API contracts.

Please create `lib/models/grid.dart`:

```dart
class Grid {
  final String gridId;
  final double latCenter;
  final double lonCenter;
  final double gos;
  final double confidence;
  final String neighborhood;

  Grid({
    required this.gridId,
    required this.latCenter,
    required this.lonCenter,
    required this.gos,
    required this.confidence,
    required this.neighborhood,
  });

  factory Grid.fromJson(Map<String, dynamic> json) {
    return Grid(
      gridId: json['grid_id'],
      latCenter: json['lat_center'],
      lonCenter: json['lon_center'],
      gos: json['gos'].toDouble(),
      confidence: json['confidence'].toDouble(),
      neighborhood: json['neighborhood'] ?? '',
    );
  }
}
```

Create `lib/models/recommendation.dart`:

```dart
class Recommendation {
  final String gridId;
  final double gos;
  final double confidence;
  final String rationale;
  final double latCenter;
  final double lonCenter;

  Recommendation({
    required this.gridId,
    required this.gos,
    required this.confidence,
    required this.rationale,
    required this.latCenter,
    required this.lonCenter,
  });

  factory Recommendation.fromJson(Map<String, dynamic> json) {
    return Recommendation(
      gridId: json['grid_id'],
      gos: json['gos'].toDouble(),
      confidence: json['confidence'].toDouble(),
      rationale: json['rationale'],
      latCenter: json['lat_center'],
      lonCenter: json['lon_center'],
    );
  }
}
```

Create `lib/models/grid_detail.dart`:

```dart
class GridDetail {
  final String gridId;
  final double gos;
  final double confidence;
  final Map<String, dynamic> metrics;
  final List<TopPost> topPosts;
  final List<Competitor> competitors;

  GridDetail({
    required this.gridId,
    required this.gos,
    required this.confidence,
    required this.metrics,
    required this.topPosts,
    required this.competitors,
  });

  factory GridDetail.fromJson(Map<String, dynamic> json) {
    return GridDetail(
      gridId: json['grid_id'],
      gos: json['gos'].toDouble(),
      confidence: json['confidence'].toDouble(),
      metrics: json['metrics'],
      topPosts: (json['top_posts'] as List)
          .map((p) => TopPost.fromJson(p))
          .toList(),
      competitors: (json['competitors'] as List)
          .map((c) => Competitor.fromJson(c))
          .toList(),
    );
  }
}

class TopPost {
  final String source;
  final String text;
  final String timestamp;
  final String? link;

  TopPost({
    required this.source,
    required this.text,
    required this.timestamp,
    this.link,
  });

  factory TopPost.fromJson(Map<String, dynamic> json) {
    return TopPost(
      source: json['source'],
      text: json['text'],
      timestamp: json['timestamp'],
      link: json['link'],
    );
  }
}

class Competitor {
  final String name;
  final double distanceKm;
  final double? rating;

  Competitor({
    required this.name,
    required this.distanceKm,
    this.rating,
  });

  factory Competitor.fromJson(Map<String, dynamic> json) {
    return Competitor(
      name: json['name'],
      distanceKm: json['distance_km'].toDouble(),
      rating: json['rating']?.toDouble(),
    );
  }
}
```
```

---

## Prompt 3: Create Mock Data Service

```
Create a mock data service for development (since backend API may not be ready).

Please create `lib/services/mock_data_service.dart`:

1. Generate mock data that matches the API response format
2. Simulate latency (add 500ms delay to mimic API calls)

Include functions:
- Future<List<Grid>> fetchGrids(String neighborhood, String category)
  * Returns 12 grids with varying GOS scores (0.3 to 0.9)
  * DHA Phase 2 coordinates
  
- Future<List<Recommendation>> fetchRecommendations(String neighborhood, String category, int limit)
  * Returns top N grids sorted by GOS
  
- Future<GridDetail> fetchGridDetail(String gridId, String category)
  * Returns detailed view with mock top posts and competitors

Use realistic mock data (refer to STARTUP_IDEA.md for example data structure).

This allows frontend development independent of backend completion.
```

---

## Prompt 4: Create Constants and Color Scheme

```
Create app constants and color scheme.

Please create `lib/utils/constants.dart`:

```dart
class AppConstants {
  static const String appName = 'StartSmart';
  static const String defaultNeighborhood = 'DHA-Phase2';
  static const List<String> categories = ['Gym', 'Cafe'];
  static const List<String> neighborhoods = ['DHA Phase 2'];
  
  // Map configuration
  static const double karachiLat = 24.8270;
  static const double karachiLon = 67.0595;
  static const double defaultZoom = 14.0;
  
  // API endpoints (for when backend is ready)
  static const String baseUrl = 'http://localhost:8000/api/v1';
}
```

Create `lib/utils/colors.dart`:

```dart
import 'package:flutter/material.dart';

class AppColors {
  // GOS heatmap colors
  static Color gosToColor(double gos) {
    if (gos >= 0.7) return const Color(0xFF00C853); // Green (high opportunity)
    if (gos >= 0.4) return const Color(0xFFFFC107); // Amber (medium)
    return const Color(0xFFE53935); // Red (low opportunity)
  }
  
  static const Color primary = Color(0xFF1976D2);
  static const Color secondary = Color(0xFF00C853);
  static const Color background = Color(0xFFF5F5F5);
  static const Color cardBackground = Colors.white;
  static const Color textPrimary = Color(0xFF212121);
  static const Color textSecondary = Color(0xFF757575);
}
```
```

---

## Prompt 5: Create Riverpod Providers

```
Create state management providers using Riverpod.

Please create `lib/providers/selection_provider.dart`:

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

final selectedCategoryProvider = StateProvider<String>((ref) => 'Gym');
final selectedNeighborhoodProvider = StateProvider<String>((ref) => 'DHA-Phase2');
final selectedGridProvider = StateProvider<String?>((ref) => null);
```

Create `lib/providers/data_provider.dart`:

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/grid.dart';
import '../models/recommendation.dart';
import '../services/mock_data_service.dart';

final mockDataService = MockDataService();

final gridsProvider = FutureProvider.family<List<Grid>, Map<String, String>>((ref, params) async {
  return mockDataService.fetchGrids(params['neighborhood']!, params['category']!);
});

final recommendationsProvider = FutureProvider.family<List<Recommendation>, Map<String, dynamic>>((ref, params) async {
  return mockDataService.fetchRecommendations(
    params['neighborhood'] as String,
    params['category'] as String,
    params['limit'] as int,
  );
});

final gridDetailProvider = FutureProvider.family<GridDetail, Map<String, String>>((ref, params) async {
  return mockDataService.fetchGridDetail(params['gridId']!, params['category']!);
});
```
```

---

## Prompt 6: Create Landing Screen

```
Create the landing screen with category and neighborhood selection.

Please create `lib/screens/landing_screen.dart`:

1. Simple welcome message: "Find the Best Location for Your Business"
2. Dropdown for category selection (Gym, Cafe)
3. Display selected neighborhood (DHA Phase 2 - only one for MVP)
4. Large "Find Locations" button
5. On button press: navigate to MapScreen

Design:
- Center-aligned content
- Use AppColors for theming
- Responsive padding
- Material 3 design
- Include StartSmart logo placeholder (Text widget for MVP)

Navigation:
- Use Navigator.push to MapScreen
- Pass selected category via constructor

Keep it simple and clean. Focus on functionality over aesthetics for MVP.
```

---

## Prompt 7: Create Heatmap Overlay Widget

```
Create the heatmap overlay for the map.

Please create `lib/widgets/heatmap_overlay.dart`:

This widget displays grid cells as colored polygons on the map.

1. Takes List<Grid> as input
2. For each grid:
   - Calculate bounds (±0.01 degrees from center for ~0.5km²)
   - Create polygon with 4 corners
   - Color based on GOS score (use AppColors.gosToColor)
   - Add slight transparency (opacity: 0.6)
   
3. Use flutter_map PolygonLayer

4. On tap: call onGridTapped(Grid) callback

Return a PolygonLayer widget with all grid polygons.

Include border for each grid (white, 2px width).
```

---

## Prompt 8: Create Map Screen (Part 1 - Map Display)

```
Create the main map screen.

Please create `lib/screens/map_screen.dart`:

1. Use flutter_map to display OpenStreetMap
2. Center on Karachi (use AppConstants coordinates)
3. Default zoom: 14 (shows neighborhood clearly)

4. Display layers:
   - OSM tile layer
   - Heatmap overlay (using HeatmapOverlay widget)
   - Marker for selected grid (if any)

5. AppBar:
   - Title: "StartSmart - {category}"
   - Back button to landing

6. Use Riverpod to:
   - Watch selectedCategoryProvider
   - Watch selectedNeighborhoodProvider
   - Fetch grids using gridsProvider

7. Show loading indicator while grids load

8. Handle errors gracefully (show SnackBar)

This is Part 1 - just the map display. Part 2 will add recommendations panel.
```

---

## Prompt 9: Create Recommendation Card Widget

```
Create the recommendation card widget.

Please create `lib/widgets/recommendation_card.dart`:

This displays a single recommendation in a card format.

Layout:
1. Grid ID as title (e.g., "DHA-Phase2-Cell-07")
2. Large GOS badge (circular, colored based on score)
3. Confidence score (small text, e.g., "78% confident")
4. Rationale (1-2 line text)
5. "View Details" button

Styling:
- Card with elevation
- Padding: 16px
- Rounded corners
- Color accent based on GOS (green/amber/red)
- Material 3 design

On tap: navigate to GridDetailScreen passing gridId.

Make it visually appealing but simple.
```

---

## Prompt 10: Create Map Screen (Part 2 - Recommendations Panel)

```
Update the Map Screen to include a recommendations panel.

Update `lib/screens/map_screen.dart`:

1. Add a bottom sheet (DraggableScrollableSheet) showing recommendations
2. Fetch recommendations using recommendationsProvider (top 3)
3. Display each recommendation using RecommendationCard widget
4. Initial height: 30% of screen, expandable to 70%

5. When a recommendation card is tapped:
   - Set selectedGridProvider to that grid_id
   - Center map on that grid
   - Add a marker on the grid

6. Add a legend in the top-right corner:
   - Small colored boxes showing GOS ranges
   - "High (0.7+)", "Medium (0.4-0.7)", "Low (<0.4)"

7. Include a filter button in AppBar (for future: time window filter - show placeholder for MVP)

Layout:
- Stack with:
  * Map layer
  * DraggableScrollableSheet (recommendations)
  * Positioned legend widget

Ensure smooth UX with no jank when scrolling sheet.
```

---

## Prompt 11: Create Grid Detail Screen

```
Create the detailed grid view screen.

Please create `lib/screens/grid_detail_screen.dart`:

1. AppBar: Grid ID as title, back button

2. Sections (scrollable):
   
   a) **Header Card**:
      - Large GOS score (circular gauge or large number)
      - Confidence score
      - Grid coordinates (lat, lon)
   
   b) **Metrics Card**:
      - Business count
      - Instagram volume
      - Reddit mentions
      - Display as icon + number pairs
   
   c) **"Why this area?" Card**:
      - Title: "What people are saying"
      - List of top 3 posts:
        * Source icon (Instagram/Reddit placeholder)
        * Text snippet (truncated to 2 lines)
        * Timestamp (relative: "2 days ago")
        * Expandable to show full text
   
   d) **Competitors Card**:
      - Title: "Existing businesses nearby"
      - List of competitors:
        * Name
        * Distance (e.g., "0.3 km away")
        * Rating (stars or number)
   
   e) **Action Buttons** (bottom):
      - "Save Location" (show toast: "Saved!" for MVP)
      - "Share" (future feature - disabled for MVP)

3. Use Riverpod gridDetailProvider to fetch data
4. Show loading state while fetching
5. Handle errors

Design:
- Cards with elevation
- Good spacing between sections
- Icons for visual appeal
- Responsive to different screen sizes
```

---

## Prompt 12: Update Main.dart and Navigation

```
Set up the main app entry point and navigation.

Update `lib/main.dart`:

1. Wrap app with ProviderScope (Riverpod requirement)

2. MaterialApp configuration:
   - Title: 'StartSmart'
   - Theme: Material 3 with AppColors
   - Initial route: LandingScreen
   - Define routes for all 3 screens

3. Global theme:
   - Primary color: AppColors.primary
   - Scaffold background: AppColors.background
   - Card theme: white background with elevation
   - AppBar theme: primary color, white text

4. Disable debug banner

Full app structure:
```dart
void main() {
  runApp(const ProviderScope(child: MyApp()));
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'StartSmart',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        // ... theme configuration
      ),
      home: const LandingScreen(),
    );
  }
}
```

Test navigation flow: Landing -> Map -> GridDetail -> back to Map -> back to Landing
```

---

## Prompt 13: Create API Service (for Backend Integration)

```
Create the real API service (for when backend is ready).

Please create `lib/services/api_service.dart`:

1. Use http package for API calls
2. Base URL from AppConstants.baseUrl
3. Implement same methods as MockDataService:
   - fetchGrids
   - fetchRecommendations
   - fetchGridDetail

4. Add error handling:
   - Network errors -> throw custom exception
   - 404 -> throw 'Not found'
   - 500 -> throw 'Server error'

5. Parse JSON responses into models

6. Add timeout (10 seconds)

7. Include headers: Content-Type: application/json

Later, you'll switch from MockDataService to ApiService by changing the provider.

For MVP, keep using MockDataService until backend Phase 4 is complete.
```

---

## Prompt 14: Add Polish and Responsiveness

```
Add final polish to the UI.

Please update all screens to:

1. Handle empty states:
   - No grids found -> show message "No data available"
   - No recommendations -> show "No recommendations yet"

2. Add pull-to-refresh on map screen:
   - Refresh grids data
   - Show loading indicator

3. Add error states:
   - Network error -> show retry button
   - Timeout -> show helpful message

4. Improve loading states:
   - Use CircularProgressIndicator with message
   - Shimmer effect for cards (optional, use placeholder for MVP)

5. Add animations:
   - Fade-in for cards
   - Smooth transitions between screens

6. Ensure responsiveness:
   - Test on mobile (360x640)
   - Test on tablet (768x1024)
   - Test on web (1920x1080)

7. Accessibility:
   - Add Semantics labels
   - Ensure sufficient color contrast
   - Support text scaling

Keep changes minimal but impactful for MVP.
```

---

## Prompt 15: Create Integration Test

```
Create a Flutter integration test.

Please create `integration_test/app_test.dart`:

1. Test full user journey:
   - Start app
   - Select category
   - Tap "Find Locations"
   - Verify map loads
   - Verify recommendations appear
   - Tap first recommendation
   - Verify detail screen loads
   - Go back to map
   - Go back to landing

2. Use flutter_test package

3. Mock API responses (use mock_data_service)

4. Verify key UI elements appear:
   - Map tiles render
   - Heatmap polygons present
   - Recommendation cards visible
   - Detail screen sections present

Run test:
```powershell
flutter test integration_test/app_test.dart
```

Also create widget tests for individual widgets:
- `test/widgets/recommendation_card_test.dart`
- `test/widgets/heatmap_overlay_test.dart`

Coverage target: ≥70% for widgets
```

---

## Prompt 16: Build and Test Web Version

```
Build the Flutter web version for demo.

Run:
```powershell
cd frontend
flutter build web --release
```

Test locally:
```powershell
# Install a simple HTTP server
python -m http.server 8080 -d build/web

# Open browser: http://localhost:8080
```

Verify:
- Map tiles load correctly
- All screens navigate properly
- Mock data displays
- No console errors
- Responsive on desktop browsers

Take screenshots for documentation:
- Landing screen
- Map with heatmap
- Recommendations panel
- Grid detail screen

Save to `docs/screenshots/`
```

---

## Prompt 17: Update PHASE_LOG.md with Phase 3 Handoff

```
Phase 3 is complete. Update PHASE_LOG.md with the Phase 3 handoff entry.

Append to PHASE_LOG.md following the format from IMPLEMENTATION_PLAN.md Phase 3 section.

Fill in:
- Your name as owner
- Completion date
- All files created (Dart files with line counts)
- Screenshots attached
- Test results (integration test, widget tests)
- Known issues (e.g., slow heatmap rendering)
- Instructions for Phase 4 developer on how to integrate real API

Include:
- Dependencies in pubspec.yaml
- Build commands for web/Android/iOS
- How to switch from MockDataService to ApiService
- Expected API response formats (so Phase 4 knows what to return)

Critical for Phase 4:
- Document exact API endpoint contracts frontend expects
- Include example responses frontend can parse
- Note any deviations from contracts/api_spec.yaml
```

---

## Phase 3 Completion Checklist

Before moving to Phase 4, verify:

- [ ] All 3 screens implemented and navigable
- [ ] Heatmap displays 12 colored grid cells
- [ ] Recommendations panel shows top-3 grids
- [ ] Grid detail screen shows metrics, posts, competitors
- [ ] Mock data service provides realistic data
- [ ] Integration test passes
- [ ] Widget tests pass (≥70% coverage)
- [ ] Web build successful and tested in browser
- [ ] Screenshots captured
- [ ] PHASE_LOG.md updated with comprehensive handoff
- [ ] No critical UI bugs (app doesn't crash)

**CRITICAL VALIDATION**:
1. User flow test: Can complete full journey without errors?
2. Visual test: Does heatmap color coding make sense (green = high GOS)?
3. Data test: Do top recommendations match highest GOS scores?
4. Responsive test: Works on mobile, tablet, and desktop?

**IMPORTANT**: Phase 4 will replace MockDataService with real API. Document the exact contract frontend expects.
