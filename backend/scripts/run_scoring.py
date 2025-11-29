"""
Command-Line Tool for Running the Scoring Engine

This script provides a user-friendly interface for:
- Scoring all grid cells for a category
- Viewing top recommendations by neighborhood
- Recomputing scores on demand

Usage:
    python scripts/run_scoring.py --category Gym
    python scripts/run_scoring.py --category Gym --neighborhood "DHA Phase 2" --top 5
    python scripts/run_scoring.py --category Cafe --recompute

Phase 2 - Analytics & Scoring Engine
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)  # Auto-reset colors after each print
    COLORAMA_AVAILABLE = True
except ImportError:
    # Fallback if colorama not installed
    COLORAMA_AVAILABLE = False
    class Fore:
        RED = GREEN = YELLOW = BLUE = CYAN = MAGENTA = WHITE = RESET = ""
    class Back:
        RED = GREEN = YELLOW = BLUE = CYAN = MAGENTA = WHITE = RESET = ""
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ""

from src.services.scoring_service import score_all_grids, get_top_recommendations


def print_header(text: str):
    """Print a formatted header."""
    if COLORAMA_AVAILABLE:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 70}")
        print(f"{text}")
        print(f"{'=' * 70}{Style.RESET_ALL}\n")
    else:
        print(f"\n{'=' * 70}")
        print(f"{text}")
        print(f"{'=' * 70}\n")


def print_success(text: str):
    """Print success message in green."""
    if COLORAMA_AVAILABLE:
        print(f"{Fore.GREEN}[OK] {text}{Style.RESET_ALL}")
    else:
        print(f"[OK] {text}")


def print_error(text: str):
    """Print error message in red."""
    if COLORAMA_AVAILABLE:
        print(f"{Fore.RED}[ERROR] {text}{Style.RESET_ALL}")
    else:
        print(f"[ERROR] {text}")


def print_warning(text: str):
    """Print warning message in yellow."""
    if COLORAMA_AVAILABLE:
        print(f"{Fore.YELLOW}[WARNING] {text}{Style.RESET_ALL}")
    else:
        print(f"[WARNING] {text}")


def print_info(text: str):
    """Print info message in blue."""
    if COLORAMA_AVAILABLE:
        print(f"{Fore.BLUE}[INFO] {text}{Style.RESET_ALL}")
    else:
        print(f"[INFO] {text}")


def print_summary_stats(results: list):
    """
    Print summary statistics for scored grids.
    
    Args:
        results: List of scored grid dictionaries
    """
    if not results:
        print_warning("No grids were scored.")
        return
    
    gos_values = [r['gos'] for r in results]
    min_gos = min(gos_values)
    max_gos = max(gos_values)
    avg_gos = sum(gos_values) / len(gos_values)
    
    print_header("SCORING SUMMARY")
    
    print(f"Total grids scored: {Fore.WHITE}{Style.BRIGHT}{len(results)}{Style.RESET_ALL}")
    print(f"GOS Range: {Fore.RED}{min_gos:.3f}{Style.RESET_ALL} (min) to "
          f"{Fore.GREEN}{max_gos:.3f}{Style.RESET_ALL} (max)")
    print(f"Average GOS: {Fore.YELLOW}{avg_gos:.3f}{Style.RESET_ALL}")
    
    # Opportunity distribution
    high = sum(1 for g in gos_values if g >= 0.7)
    medium = sum(1 for g in gos_values if 0.4 <= g < 0.7)
    low = sum(1 for g in gos_values if g < 0.4)
    
    print(f"\nOpportunity Distribution:")
    print(f"  {Fore.GREEN}HIGH{Style.RESET_ALL} (GOS ≥ 0.7):   {high} grids")
    print(f"  {Fore.YELLOW}MEDIUM{Style.RESET_ALL} (0.4-0.7):  {medium} grids")
    print(f"  {Fore.RED}LOW{Style.RESET_ALL} (GOS < 0.4):   {low} grids")
    
    # Top 3 grids
    top_3 = sorted(results, key=lambda x: x['gos'], reverse=True)[:3]
    
    print(f"\n{Fore.CYAN}Top 3 Opportunity Grids:{Style.RESET_ALL}")
    for i, grid in enumerate(top_3, 1):
        gos_color = Fore.GREEN if grid['gos'] >= 0.7 else (Fore.YELLOW if grid['gos'] >= 0.4 else Fore.RED)
        print(f"\n  {i}. {Fore.WHITE}{Style.BRIGHT}{grid['grid_id']}{Style.RESET_ALL}")
        print(f"     GOS: {gos_color}{grid['gos']:.3f}{Style.RESET_ALL} | "
              f"Confidence: {Fore.CYAN}{grid['confidence']:.3f}{Style.RESET_ALL}")
        print(f"     {grid['rationale']}")
        print(f"     Metrics: {grid['business_count']} businesses, "
              f"{grid['instagram_volume']} Instagram, {grid['reddit_mentions']} Reddit")


def print_recommendations(recommendations: list, neighborhood: str, category: str, top: int):
    """
    Print recommendations in a formatted, readable way.
    
    Args:
        recommendations: List of recommendation dictionaries
        neighborhood: Neighborhood name
        category: Business category
        top: Number of top recommendations
    """
    if not recommendations:
        print_warning(f"No recommendations found for {category} in {neighborhood}")
        return
    
    print_header(f"Top {min(top, len(recommendations))} Recommendations: {category} in {neighborhood}")
    
    for i, rec in enumerate(recommendations, 1):
        # Grid ID and rank
        print(f"\n{Fore.WHITE}{Style.BRIGHT}{i}. {rec['grid_id']}{Style.RESET_ALL}")
        
        # GOS and Confidence
        gos_color = Fore.GREEN if rec['gos'] >= 0.7 else (Fore.YELLOW if rec['gos'] >= 0.4 else Fore.RED)
        print(f"   GOS: {gos_color}{rec['gos']:.3f}{Style.RESET_ALL} | "
              f"Confidence: {Fore.CYAN}{rec['confidence']:.3f}{Style.RESET_ALL}")
        
        # Rationale
        print(f"   {Fore.MAGENTA}Rationale:{Style.RESET_ALL} {rec['rationale']}")
        
        # Location
        print(f"   {Fore.BLUE}Location:{Style.RESET_ALL} {rec['lat_center']:.5f}, {rec['lon_center']:.5f}")
        
        # Metrics breakdown
        print(f"   {Fore.YELLOW}Metrics:{Style.RESET_ALL} "
              f"{rec['business_count']} businesses, "
              f"{rec['instagram_volume']} Instagram posts, "
              f"{rec['reddit_mentions']} Reddit mentions")
        
        # Top posts (if available)
        if rec.get('top_posts') and len(rec['top_posts']) > 0:
            print(f"   {Fore.CYAN}Top Demand Signals:{Style.RESET_ALL}")
            for j, post in enumerate(rec['top_posts'][:2], 1):  # Show max 2 posts
                text = post['text'][:60] + "..." if len(post['text']) > 60 else post['text']
                print(f"     {j}. \"{text}\"")
        
        # Competitors (if available)
        if rec.get('competitors') and len(rec['competitors']) > 0:
            print(f"   {Fore.RED}Nearby Competitors:{Style.RESET_ALL}")
            for j, comp in enumerate(rec['competitors'][:3], 1):  # Show max 3 competitors
                rating_str = f"{comp['rating']:.1f}★" if comp['rating'] else "No rating"
                print(f"     {j}. {comp['name']} - {rating_str} ({comp['distance_km']}km)")


def check_recompute_needed(category: str) -> bool:
    """
    Check if grid_metrics already has data for this category.
    
    Args:
        category: Business category
    
    Returns:
        True if recomputation needed (no existing data)
    """
    try:
        from src.database.connection import get_session
        from src.database.models import GridMetricsModel
        
        with get_session() as session:
            count = session.query(GridMetricsModel).filter_by(category=category).count()
            return count == 0
    except Exception as e:
        print_warning(f"Could not check existing data: {e}")
        return True


def main():
    """Main entry point for the scoring CLI tool."""
    parser = argparse.ArgumentParser(
        description="Run the StartSmart Scoring Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Score all grids for Gym category
  python scripts/run_scoring.py --category Gym
  
  # Get top 5 recommendations for DHA Phase 2
  python scripts/run_scoring.py --category Gym --neighborhood "DHA Phase 2" --top 5
  
  # Force recomputation of scores
  python scripts/run_scoring.py --category Cafe --recompute
        """
    )
    
    parser.add_argument(
        '--category',
        required=True,
        choices=['Gym', 'Cafe'],
        help='Business category to score (Gym or Cafe)'
    )
    
    parser.add_argument(
        '--neighborhood',
        type=str,
        help='Neighborhood name for recommendations (e.g., "DHA Phase 2")'
    )
    
    parser.add_argument(
        '--top',
        type=int,
        default=3,
        help='Number of top recommendations to show (default: 3)'
    )
    
    parser.add_argument(
        '--recompute',
        action='store_true',
        help='Force recomputation even if scores already exist'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_header("StartSmart Scoring Engine - Phase 2")
    print(f"Category: {Fore.WHITE}{Style.BRIGHT}{args.category}{Style.RESET_ALL}")
    print(f"Timestamp: {Fore.CYAN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
    
    # Check if recomputation is needed
    needs_recompute = check_recompute_needed(args.category)
    
    if not needs_recompute and not args.recompute:
        print_info(f"Scores already exist for {args.category}. Use --recompute to force recalculation.")
        
        # If only showing recommendations, skip scoring
        if args.neighborhood:
            print_info("Fetching recommendations from existing data...")
            try:
                recommendations = get_top_recommendations(args.neighborhood, args.category, args.top)
                print_recommendations(recommendations, args.neighborhood, args.category, args.top)
                print_success("Recommendations retrieved successfully!")
                return 0
            except Exception as e:
                print_error(f"Failed to get recommendations: {e}")
                return 1
        else:
            print_info("Use --neighborhood to view recommendations, or --recompute to recalculate scores.")
            return 0
    
    # Run scoring pipeline
    if args.recompute:
        print_warning("Forcing recomputation of all scores...")
    
    print_info(f"Starting scoring pipeline for {args.category}...")
    
    try:
        # Score all grids
        results = score_all_grids(args.category)
        
        # Print summary
        print_summary_stats(results)
        
        print_success(f"Successfully scored {len(results)} grids for {args.category}!")
        
        # If neighborhood specified, show recommendations
        if args.neighborhood:
            print_info(f"\nFetching top {args.top} recommendations for {args.neighborhood}...")
            recommendations = get_top_recommendations(args.neighborhood, args.category, args.top)
            print_recommendations(recommendations, args.neighborhood, args.category, args.top)
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}[COMPLETE] Scoring engine finished successfully!{Style.RESET_ALL}\n")
        return 0
        
    except Exception as e:
        print_error(f"Scoring pipeline failed: {e}")
        import traceback
        print(f"\n{Fore.RED}Traceback:{Style.RESET_ALL}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
