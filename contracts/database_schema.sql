-- StartSmart MVP Database Schema
-- Phase 0: Interface Contracts
-- PostgreSQL 14+ with PostGIS extension
-- 
-- This schema is LOCKED for MVP. No ad-hoc changes allowed in later phases.
-- All tables, columns, types, and indexes are defined here.

-- Enable PostGIS extension for geospatial operations
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- Grid Cells Table
-- ============================================================================
-- Computed once during Phase 0, static for MVP
-- Represents ~0.5 km² grid cells covering 5 pilot neighborhoods

CREATE TABLE grid_cells (
    grid_id VARCHAR(50) PRIMARY KEY,
    neighborhood VARCHAR(100) NOT NULL,
    lat_center DECIMAL(10, 7) NOT NULL,
    lon_center DECIMAL(10, 7) NOT NULL,
    lat_north DECIMAL(10, 7) NOT NULL,
    lat_south DECIMAL(10, 7) NOT NULL,
    lon_east DECIMAL(10, 7) NOT NULL,
    lon_west DECIMAL(10, 7) NOT NULL,
    area_km2 DECIMAL(5, 2) DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for grid_cells
CREATE INDEX idx_grid_neighborhood ON grid_cells(neighborhood);
CREATE INDEX idx_grid_center ON grid_cells(lat_center, lon_center);

-- ============================================================================
-- Businesses Table
-- ============================================================================
-- Populated from Google Places API (real data for MVP)
-- One row per business location

CREATE TABLE businesses (
    business_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    lat DECIMAL(10, 7) NOT NULL,
    lon DECIMAL(10, 7) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'Gym', 'Cafe', etc.
    rating DECIMAL(2, 1), -- 0.0 to 5.0
    review_count INTEGER DEFAULT 0,
    source VARCHAR(50) DEFAULT 'google_places',
    grid_id VARCHAR(50) REFERENCES grid_cells(grid_id) ON DELETE SET NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for businesses
CREATE INDEX idx_business_category ON businesses(category);
CREATE INDEX idx_business_grid_category ON businesses(grid_id, category);
CREATE INDEX idx_business_location ON businesses(lat, lon);
CREATE INDEX idx_business_source ON businesses(source);

-- ============================================================================
-- Social Posts Table
-- ============================================================================
-- Synthetic data for MVP (is_simulated = TRUE)
-- Future phases will add real Instagram/Reddit data
-- One row per social media post or mention

CREATE TABLE social_posts (
    post_id VARCHAR(100) PRIMARY KEY,
    source VARCHAR(50) NOT NULL, -- 'instagram', 'reddit', 'simulated'
    text TEXT,
    timestamp TIMESTAMP,
    lat DECIMAL(10, 7),
    lon DECIMAL(10, 7),
    grid_id VARCHAR(50) REFERENCES grid_cells(grid_id) ON DELETE SET NULL,
    post_type VARCHAR(50), -- 'demand', 'complaint', 'mention'
    engagement_score INTEGER DEFAULT 0, -- likes, upvotes, etc.
    is_simulated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for social_posts
CREATE INDEX idx_post_grid_type ON social_posts(grid_id, post_type);
CREATE INDEX idx_post_source ON social_posts(source);
CREATE INDEX idx_post_timestamp ON social_posts(timestamp);
CREATE INDEX idx_post_simulated ON social_posts(is_simulated);
CREATE INDEX idx_post_location ON social_posts(lat, lon) WHERE lat IS NOT NULL AND lon IS NOT NULL;

-- ============================================================================
-- Grid Metrics Table
-- ============================================================================
-- Computed by scoring engine (Phase 2)
-- One row per (grid_id, category) combination
-- Contains Gap Opportunity Score (GOS) and all supporting metrics

CREATE TABLE grid_metrics (
    id SERIAL PRIMARY KEY,
    grid_id VARCHAR(50) REFERENCES grid_cells(grid_id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    business_count INTEGER DEFAULT 0,
    instagram_volume INTEGER DEFAULT 0,
    reddit_mentions INTEGER DEFAULT 0,
    gos DECIMAL(4, 3), -- 0.000 to 1.000 (Gap Opportunity Score)
    confidence DECIMAL(4, 3), -- 0.000 to 1.000
    top_posts_json JSONB, -- Top 3 posts with text + links
    competitors_json JSONB, -- List of nearby businesses
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (grid_id, category)
);

-- Indexes for grid_metrics
CREATE INDEX idx_metrics_gos ON grid_metrics(gos DESC);
CREATE INDEX idx_metrics_category_gos ON grid_metrics(category, gos DESC);
CREATE INDEX idx_metrics_grid ON grid_metrics(grid_id);
CREATE INDEX idx_metrics_last_updated ON grid_metrics(last_updated);

-- JSONB indexes for efficient querying
CREATE INDEX idx_metrics_top_posts ON grid_metrics USING GIN (top_posts_json);
CREATE INDEX idx_metrics_competitors ON grid_metrics USING GIN (competitors_json);

-- ============================================================================
-- User Feedback Table
-- ============================================================================
-- Optional for MVP, prepared for Phase 4
-- Captures user validation of recommendations

CREATE TABLE user_feedback (
    id SERIAL PRIMARY KEY,
    grid_id VARCHAR(50) REFERENCES grid_cells(grid_id) ON DELETE CASCADE,
    category VARCHAR(50),
    rating INTEGER CHECK (rating IN (-1, 1)), -- thumbs down (-1) / thumbs up (1)
    comment TEXT,
    user_email VARCHAR(255), -- nullable for guest users
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for user_feedback
CREATE INDEX idx_feedback_grid ON user_feedback(grid_id);
CREATE INDEX idx_feedback_category ON user_feedback(category);
CREATE INDEX idx_feedback_rating ON user_feedback(rating);
CREATE INDEX idx_feedback_created ON user_feedback(created_at);

-- ============================================================================
-- Constraints and Comments
-- ============================================================================

-- Add table comments for documentation
COMMENT ON TABLE grid_cells IS 'Static grid cells covering pilot neighborhoods (~0.5 km² each)';
COMMENT ON TABLE businesses IS 'Business locations from Google Places API';
COMMENT ON TABLE social_posts IS 'Social media posts (synthetic for MVP, real data post-MVP)';
COMMENT ON TABLE grid_metrics IS 'Computed opportunity scores per grid per category';
COMMENT ON TABLE user_feedback IS 'User validation feedback on recommendations';

-- Add column comments for critical fields
COMMENT ON COLUMN grid_metrics.gos IS 'Gap Opportunity Score: 0.0 (low) to 1.0 (high opportunity)';
COMMENT ON COLUMN grid_metrics.confidence IS 'Confidence score based on data volume and recency';
COMMENT ON COLUMN social_posts.is_simulated IS 'TRUE for synthetic data, FALSE for real scraped data';
COMMENT ON COLUMN businesses.source IS 'Data source identifier (google_places, manual, etc.)';

-- ============================================================================
-- End of Schema Definition
-- ============================================================================
-- Schema version: 1.0.0
-- Last updated: 2025-11-05
-- Compatible with: PostgreSQL 14+, PostGIS 3.0+
