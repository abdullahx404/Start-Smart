import '../models/grid.dart';
import '../models/recommendation.dart';
import '../models/grid_detail.dart';

/// Mock data service for offline/demo mode
/// Provides sample data when backend is unavailable
class MockDataService {
  /// Get mock neighborhoods
  List<Map<String, dynamic>> getNeighborhoods() {
    return [
      {'id': 'DHA-Phase2', 'name': 'DHA Phase 2', 'grid_count': 9},
      {'id': 'Clifton-Block2', 'name': 'Clifton Block 2', 'grid_count': 9},
    ];
  }

  /// Get mock grids for a neighborhood
  List<Grid> getGrids({
    required String neighborhood,
    required String category,
  }) {
    if (neighborhood == 'DHA-Phase2') {
      return _getDHAPhase2Grids();
    } else if (neighborhood == 'Clifton-Block2') {
      return _getCliftonBlock2Grids();
    }
    return [];
  }

  /// Get mock recommendations
  List<Recommendation> getRecommendations({
    required String neighborhood,
    required String category,
    int limit = 3,
  }) {
    final grids = getGrids(neighborhood: neighborhood, category: category);
    grids.sort((a, b) => b.gos.compareTo(a.gos));

    return grids.take(limit).map((grid) {
      return Recommendation(
        gridId: grid.gridId,
        gos: grid.gos,
        confidence: grid.confidence,
        rationale: _generateRationale(grid),
        latCenter: grid.latCenter,
        lonCenter: grid.lonCenter,
        businessCount: grid.businessCount,
        instagramVolume: grid.instagramVolume,
        redditMentions: grid.redditMentions,
        topPosts: _getMockTopPosts(),
        competitors: _getMockCompetitors(grid.businessCount),
      );
    }).toList();
  }

  /// Get mock grid detail
  GridDetail getGridDetail({required String gridId, required String category}) {
    // Find the grid from mock data
    final allGrids = [..._getDHAPhase2Grids(), ..._getCliftonBlock2Grids()];

    final grid = allGrids.firstWhere(
      (g) => g.gridId == gridId,
      orElse: () => allGrids.first,
    );

    return GridDetail(
      gridId: grid.gridId,
      neighborhood: grid.neighborhood,
      latCenter: grid.latCenter,
      lonCenter: grid.lonCenter,
      latNorth: grid.latNorth,
      latSouth: grid.latSouth,
      lonEast: grid.lonEast,
      lonWest: grid.lonWest,
      gos: grid.gos,
      confidence: grid.confidence,
      metrics: GridMetrics(
        businessCount: grid.businessCount,
        instagramVolume: grid.instagramVolume,
        redditMentions: grid.redditMentions,
        avgRating: 4.2,
        totalReviews: 150,
      ),
      topPosts: _getMockTopPosts(),
      competitors: _getMockCompetitors(grid.businessCount),
      rationale: _generateRationale(grid),
    );
  }

  /// DHA Phase 2 mock grids (3x3 = 9 cells)
  List<Grid> _getDHAPhase2Grids() {
    const baseLat = 24.8233;
    const baseLon = 67.0545;
    const cellSize = 0.0045; // ~0.5km

    final gosScores = [0.666, 0.666, 0.58, 0.58, 0.54, 0.54, 0.52, 0.50, 0.48];
    final businessCounts = [0, 0, 0, 1, 2, 2, 3, 4, 5];
    final instagramVolumes = [28, 25, 38, 30, 25, 20, 18, 15, 12];
    final redditMentions = [47, 50, 12, 20, 25, 30, 22, 15, 18];

    final grids = <Grid>[];
    int index = 0;

    for (int row = 0; row < 3; row++) {
      for (int col = 0; col < 3; col++) {
        final cellNum = (row * 3 + col + 1).toString().padLeft(2, '0');
        final latCenter = baseLat + (row * cellSize);
        final lonCenter = baseLon + (col * cellSize);

        grids.add(
          Grid(
            gridId: 'DHA-Phase2-Cell-$cellNum',
            neighborhood: 'DHA Phase 2',
            latCenter: latCenter,
            lonCenter: lonCenter,
            latNorth: latCenter + cellSize / 2,
            latSouth: latCenter - cellSize / 2,
            lonEast: lonCenter + cellSize / 2,
            lonWest: lonCenter - cellSize / 2,
            gos: gosScores[index],
            confidence: 1.0,
            businessCount: businessCounts[index],
            instagramVolume: instagramVolumes[index],
            redditMentions: redditMentions[index],
          ),
        );
        index++;
      }
    }

    return grids;
  }

  /// Clifton Block 2 mock grids (3x3 = 9 cells)
  List<Grid> _getCliftonBlock2Grids() {
    const baseLat = 24.8068;
    const baseLon = 67.0235;
    const cellSize = 0.0045;

    final gosScores = [
      0.933,
      0.932,
      0.757,
      0.757,
      0.719,
      0.68,
      0.65,
      0.60,
      0.55,
    ];
    final businessCounts = [0, 0, 0, 0, 1, 2, 2, 3, 4];
    final instagramVolumes = [75, 75, 50, 50, 40, 35, 30, 25, 20];
    final redditMentions = [75, 75, 50, 50, 40, 35, 30, 25, 20];

    final grids = <Grid>[];
    int index = 0;

    for (int row = 0; row < 3; row++) {
      for (int col = 0; col < 3; col++) {
        final cellNum = (row * 3 + col + 1).toString().padLeft(2, '0');
        final latCenter = baseLat + (row * cellSize);
        final lonCenter = baseLon + (col * cellSize);

        grids.add(
          Grid(
            gridId: 'Clifton-Block2-Cell-$cellNum',
            neighborhood: 'Clifton Block 2',
            latCenter: latCenter,
            lonCenter: lonCenter,
            latNorth: latCenter + cellSize / 2,
            latSouth: latCenter - cellSize / 2,
            lonEast: lonCenter + cellSize / 2,
            lonWest: lonCenter - cellSize / 2,
            gos: gosScores[index],
            confidence: 1.0,
            businessCount: businessCounts[index],
            instagramVolume: instagramVolumes[index],
            redditMentions: redditMentions[index],
          ),
        );
        index++;
      }
    }

    return grids;
  }

  /// Generate rationale text based on grid data
  String _generateRationale(Grid grid) {
    final demandLevel = grid.totalDemand > 50
        ? 'High demand'
        : grid.totalDemand > 25
        ? 'Moderate demand'
        : 'Low demand';

    final competitionLevel = grid.businessCount == 0
        ? 'no competition'
        : grid.businessCount <= 2
        ? 'low competition'
        : 'moderate competition';

    return '$demandLevel (${grid.totalDemand} signals) with $competitionLevel '
        '(${grid.businessCount} businesses)';
  }

  /// Get mock top posts
  List<TopPost> _getMockTopPosts() {
    return [
      TopPost(
        source: 'simulated',
        text: 'Looking for a good gym in this area! Any recommendations?',
        timestamp: DateTime.now()
            .subtract(const Duration(days: 5))
            .toIso8601String(),
        link: 'https://simulated.example/post1',
      ),
      TopPost(
        source: 'simulated',
        text: 'Great workout session today! #fitness #gym',
        timestamp: DateTime.now()
            .subtract(const Duration(days: 12))
            .toIso8601String(),
        link: 'https://simulated.example/post2',
      ),
      TopPost(
        source: 'simulated',
        text: 'Need a 24/7 gym nearby. Anyone know of one?',
        timestamp: DateTime.now()
            .subtract(const Duration(days: 20))
            .toIso8601String(),
        link: 'https://simulated.example/post3',
      ),
    ];
  }

  /// Get mock competitors based on count
  List<Competitor> _getMockCompetitors(int count) {
    final allCompetitors = [
      Competitor(name: 'Fitness First', distanceKm: 0.3, rating: 4.5),
      Competitor(name: 'Gold\'s Gym', distanceKm: 0.5, rating: 4.2),
      Competitor(name: 'Shapes Fitness', distanceKm: 0.7, rating: 4.0),
      Competitor(name: 'Body & Soul', distanceKm: 0.9, rating: 3.8),
      Competitor(name: 'PowerHouse Gym', distanceKm: 1.1, rating: 4.1),
    ];

    return allCompetitors.take(count).toList();
  }
}
