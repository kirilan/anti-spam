-- Migration: Add broker responses table and response type enum
-- Phase 3: Response Tracking System

-- Create response type enum
DO $$ BEGIN
    CREATE TYPE responsetype AS ENUM (
        'confirmation',
        'rejection',
        'acknowledgment',
        'request_info',
        'unknown'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Ensure UUID generation function exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create broker_responses table
CREATE TABLE IF NOT EXISTS broker_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign keys
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    deletion_request_id UUID REFERENCES deletion_requests(id) ON DELETE SET NULL,

    -- Gmail metadata
    gmail_message_id VARCHAR NOT NULL UNIQUE,
    gmail_thread_id VARCHAR,

    -- Email content
    sender_email VARCHAR NOT NULL,
    subject VARCHAR,
    body_text TEXT,
    received_date TIMESTAMP,

    -- Classification
    response_type responsetype DEFAULT 'unknown' NOT NULL,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    matched_by VARCHAR,

    -- Processing metadata
    is_processed BOOLEAN DEFAULT FALSE NOT NULL,
    processed_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_broker_responses_gmail_message_id ON broker_responses(gmail_message_id);
CREATE INDEX IF NOT EXISTS idx_broker_responses_gmail_thread_id ON broker_responses(gmail_thread_id);
CREATE INDEX IF NOT EXISTS idx_broker_responses_deletion_request_id ON broker_responses(deletion_request_id);
CREATE INDEX IF NOT EXISTS idx_broker_responses_user_id ON broker_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_broker_responses_response_type ON broker_responses(response_type);
CREATE INDEX IF NOT EXISTS idx_broker_responses_is_processed ON broker_responses(is_processed);
