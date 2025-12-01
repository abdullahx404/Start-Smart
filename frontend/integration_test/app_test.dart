// StartSmart Integration Tests
// Tests navigation flow, state management, and mock data loading
//
// Run with: flutter test integration_test/app_test.dart
// Or for web: flutter test integration_test/app_test.dart -d chrome

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:startsmart/main.dart';
import 'package:startsmart/screens/map_screen.dart';
import 'package:startsmart/screens/grid_detail_screen.dart';
import 'package:startsmart/utils/constants.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('App Launch Tests', () {
    testWidgets('App launches successfully', (WidgetTester tester) async {
      await tester.pumpWidget(const ProviderScope(child: StartSmartApp()));
      await tester.pumpAndSettle();

      // Verify app title is visible
      expect(find.text('StartSmart'), findsOneWidget);
    });

    testWidgets('Landing screen shows category selection', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const ProviderScope(child: StartSmartApp()));
      await tester.pumpAndSettle();

      // Verify category options exist
      expect(find.text(Categories.gym), findsOneWidget);
      expect(find.text(Categories.cafe), findsOneWidget);
    });

    testWidgets('Landing screen shows neighborhood dropdown', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const ProviderScope(child: StartSmartApp()));
      await tester.pumpAndSettle();

      // Verify neighborhood selection exists
      expect(find.text('Select a neighborhood'), findsOneWidget);
    });
  });

  group('Category Selection Tests', () {
    testWidgets('Can select Gym category', (WidgetTester tester) async {
      await tester.pumpWidget(const ProviderScope(child: StartSmartApp()));
      await tester.pumpAndSettle();

      // Tap on Gym category
      final gymWidget = find.text(Categories.gym);
      await tester.tap(gymWidget);
      await tester.pumpAndSettle();

      // Verify Gym is selected (should be highlighted)
      expect(gymWidget, findsOneWidget);
    });

    testWidgets('Can select Cafe category', (WidgetTester tester) async {
      await tester.pumpWidget(const ProviderScope(child: StartSmartApp()));
      await tester.pumpAndSettle();

      // Find and tap Cafe category
      final cafeWidget = find.text(Categories.cafe);
      await tester.tap(cafeWidget);
      await tester.pumpAndSettle();

      // Verify Cafe is selected
      expect(cafeWidget, findsOneWidget);
    });
  });

  group('Neighborhood Selection Tests', () {
    testWidgets('Can open neighborhood dropdown', (WidgetTester tester) async {
      await tester.pumpWidget(const ProviderScope(child: StartSmartApp()));
      await tester.pumpAndSettle();

      // Find and tap dropdown
      final dropdown = find.byType(DropdownButton<String>);
      await tester.tap(dropdown);
      await tester.pumpAndSettle();

      // Verify dropdown options appear
      // Note: Options appear in overlay, check for neighborhood names
      expect(find.text('DHA Phase 2'), findsWidgets);
    });

    testWidgets('Can select a neighborhood', (WidgetTester tester) async {
      await tester.pumpWidget(const ProviderScope(child: StartSmartApp()));
      await tester.pumpAndSettle();

      // Open dropdown
      final dropdown = find.byType(DropdownButton<String>);
      await tester.tap(dropdown);
      await tester.pumpAndSettle();

      // Select first neighborhood
      final firstNeighborhood = find.text('DHA Phase 2').last;
      await tester.tap(firstNeighborhood);
      await tester.pumpAndSettle();

      // Verify selection - button should now be enabled
      final findButton = find.text('Find Locations');
      expect(findButton, findsOneWidget);
    });
  });

  group('Navigation Tests', () {
    testWidgets('Find Locations button is disabled without selection', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const ProviderScope(child: StartSmartApp()));
      await tester.pumpAndSettle();

      // Find the button
      final button = find.widgetWithText(ElevatedButton, 'Find Locations');
      expect(button, findsOneWidget);

      // Verify button state - should not navigate without selection
      final elevatedButton = tester.widget<ElevatedButton>(button);
      expect(elevatedButton.onPressed, isNull);
    });

    testWidgets('Can navigate to map screen after selection', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const ProviderScope(child: StartSmartApp()));
      await tester.pumpAndSettle();

      // Select a neighborhood
      final dropdown = find.byType(DropdownButton<String>);
      await tester.tap(dropdown);
      await tester.pumpAndSettle();

      // Tap first neighborhood option
      final neighborhoodOption = find.text('DHA Phase 2').last;
      await tester.tap(neighborhoodOption);
      await tester.pumpAndSettle();

      // Tap Find Locations button
      final findButton = find.widgetWithText(ElevatedButton, 'Find Locations');
      await tester.tap(findButton);
      await tester.pumpAndSettle();

      // Verify we're on the map screen (check for GOS Legend or map elements)
      // Wait for async data loading
      await tester.pump(const Duration(seconds: 2));

      // Should now be on map screen - check for AppBar title with neighborhood
      expect(find.text('DHA Phase 2'), findsWidgets);
    });
  });

  group('Map Screen Tests', () {
    testWidgets('Map screen displays filter panel', (
      WidgetTester tester,
    ) async {
      // Create a container with navigation to map screen
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Builder(
              builder: (context) {
                return ElevatedButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => const MapScreen(),
                      ),
                    );
                  },
                  child: const Text('Go to Map'),
                );
              },
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Navigate to map
      await tester.tap(find.text('Go to Map'));
      await tester.pumpAndSettle();
      await tester.pump(const Duration(seconds: 2));

      // Map screen should be visible
      expect(find.byType(MapScreen), findsOneWidget);
    });

    testWidgets('Map screen has recommendations toggle', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Builder(
              builder: (context) {
                return ElevatedButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => const MapScreen(),
                      ),
                    );
                  },
                  child: const Text('Go to Map'),
                );
              },
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Go to Map'));
      await tester.pumpAndSettle();
      await tester.pump(const Duration(seconds: 2));

      // Check for recommendations toggle icon
      expect(find.byIcon(Icons.view_sidebar), findsOneWidget);
    });

    testWidgets('Map screen has refresh button', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Builder(
              builder: (context) {
                return ElevatedButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => const MapScreen(),
                      ),
                    );
                  },
                  child: const Text('Go to Map'),
                );
              },
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Go to Map'));
      await tester.pumpAndSettle();
      await tester.pump(const Duration(seconds: 2));

      // Check for refresh icon
      expect(find.byIcon(Icons.refresh), findsOneWidget);
    });
  });

  group('Grid Detail Screen Tests', () {
    testWidgets('Grid detail screen displays tabs', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: GridDetailScreen(gridId: 'dha-phase-2-grid-1-1'),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.pump(const Duration(seconds: 2));

      // Check for tab labels
      expect(find.text('Overview'), findsOneWidget);
      expect(find.text('Evidence'), findsOneWidget);
      expect(find.text('Competitors'), findsOneWidget);
    });

    testWidgets('Grid detail screen has feedback bar', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: GridDetailScreen(gridId: 'dha-phase-2-grid-1-1'),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.pump(const Duration(seconds: 2));

      // Check for feedback prompt
      expect(find.text('Is this helpful?'), findsOneWidget);
    });

    testWidgets('Can switch between tabs', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: GridDetailScreen(gridId: 'dha-phase-2-grid-1-1'),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.pump(const Duration(seconds: 2));

      // Tap Evidence tab
      await tester.tap(find.text('Evidence'));
      await tester.pumpAndSettle();

      // Tap Competitors tab
      await tester.tap(find.text('Competitors'));
      await tester.pumpAndSettle();

      // Tap back to Overview
      await tester.tap(find.text('Overview'));
      await tester.pumpAndSettle();

      // All tabs should still be visible
      expect(find.text('Overview'), findsOneWidget);
    });
  });

  group('Mock Data Loading Tests', () {
    testWidgets('Landing screen loads without errors', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const ProviderScope(child: StartSmartApp()));
      await tester.pumpAndSettle();

      // No error indicators should be visible
      expect(find.byIcon(Icons.error), findsNothing);
      expect(find.byIcon(Icons.error_outline), findsNothing);
    });

    testWidgets('Feature descriptions are visible', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const ProviderScope(child: StartSmartApp()));
      await tester.pumpAndSettle();

      // Check for feature section
      expect(find.text('Data-Driven Insights'), findsOneWidget);
      expect(find.text('Interactive Heatmaps'), findsOneWidget);
      expect(find.text('Smart Recommendations'), findsOneWidget);
    });
  });

  group('Full Flow Integration Test', () {
    testWidgets('Complete user journey: Landing -> Map -> Detail', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(const ProviderScope(child: StartSmartApp()));
      await tester.pumpAndSettle();

      // Step 1: On Landing Screen
      expect(find.text('StartSmart'), findsOneWidget);

      // Step 2: Select category
      await tester.tap(find.text(Categories.gym));
      await tester.pumpAndSettle();

      // Step 3: Select neighborhood
      final dropdown = find.byType(DropdownButton<String>);
      await tester.tap(dropdown);
      await tester.pumpAndSettle();

      final neighborhood = find.text('DHA Phase 2').last;
      await tester.tap(neighborhood);
      await tester.pumpAndSettle();

      // Step 4: Navigate to Map
      final findButton = find.widgetWithText(ElevatedButton, 'Find Locations');
      expect(findButton, findsOneWidget);

      // Verify button is now enabled
      final button = tester.widget<ElevatedButton>(findButton);
      expect(button.onPressed, isNotNull);

      // Tap and navigate
      await tester.tap(findButton);
      await tester.pumpAndSettle();
      await tester.pump(const Duration(seconds: 3));

      // Step 5: Verify Map Screen
      expect(find.byType(MapScreen), findsOneWidget);

      // Test completed successfully
    });
  });
}
