#!/usr/bin/env python3
import json, random, uuid, argparse
from datetime import datetime, timedelta
from pathlib import Path

TEMPLATES = {
    "Gym": {
        "demand": ["Looking for a good gym in {loc}. Any recommendations?", "Need a gym near {loc} with proper equipment"],
        "complaint": ["No good gyms in {loc} at all", "Why are there no proper gyms in {loc}?"],
        "mention": ["Morning workout done! #fitness #gym #{tag}", "Leg day at the gym #{tag}"]
    },
    "Cafe": {
        "demand": ["Looking for a good cafe in {loc}. Suggestions?", "Need a quiet cafe near {loc} with WiFi"],
        "complaint": ["No good cafes in {loc}!", "Why are there no decent coffee shops in {loc}?"],
        "mention": ["Coffee break! #{tag} #cafe", "Perfect latte today #{tag}"]
    }
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--grids", type=int, default=9)
    parser.add_argument("--posts-per-grid", type=int, default=50)
    parser.add_argument("--output", type=str, default="data/synthetic/")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    
    if args.seed:
        random.seed(args.seed)
    
    posts = []
    for grid_idx in range(args.grids):
        grid_id = f"DHA-Phase2-Cell-{str(grid_idx+1).zfill(2)}"
        opp = "high" if grid_idx < 2 else ("low" if grid_idx > 6 else "medium")
        count = int(args.posts_per_grid * (1.5 if opp == "high" else 0.6 if opp == "low" else 1.0))
        
        for _ in range(count):
            cat = random.choice(["Gym", "Cafe"])
            ptype = random.choices(["mention", "demand", "complaint"], 
                                  weights=[0.40 if opp=="high" else 0.60, 0.40 if opp=="high" else 0.25, 0.20 if opp=="high" else 0.15])[0]
            text = random.choice(TEMPLATES[cat][ptype]).format(loc="Phase 2", tag="DHA")
            
            posts.append({
                "post_id": str(uuid.uuid4()),
                "source": "simulated",
                "text": text,
                "timestamp": (datetime.utcnow() - timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "lat": round(24.8210 + random.random() * 0.0135, 6),
                "lon": round(67.0520 + random.random() * 0.0150, 6),
                "grid_id": grid_id,
                "post_type": ptype,
                "engagement_score": random.randint(5 if ptype=="mention" else 20, 100 if opp=="high" else 50),
                "is_simulated": True
            })
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "social_posts_v1.json"
    
    with open(output_file, "w") as f:
        json.dump(posts, f, indent=2)
    
    print(f"Generated {len(posts)} posts -> {output_file}")
    return 0

if __name__ == "__main__":
    exit(main())
