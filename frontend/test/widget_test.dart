// StartSmart widget tests

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:startsmart/main.dart';

void main() {
  testWidgets('StartSmart app launches successfully', (
    WidgetTester tester,
  ) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const ProviderScope(child: StartSmartApp()));

    // Verify that the app title is displayed
    expect(find.text('StartSmart'), findsOneWidget);

    // Verify that the category selection is present
    expect(find.text('What type of business?'), findsOneWidget);

    // Verify that the neighborhood selection is present
    expect(find.text('Which neighborhood?'), findsOneWidget);

    // Verify that the Find Locations button is present
    expect(find.text('Find Locations'), findsOneWidget);
  });
}
