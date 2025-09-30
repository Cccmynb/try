-- Extensions (idempotent)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Domain: create only if missing (idempotent)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'small_posint') THEN
    CREATE DOMAIN small_posint AS INT CHECK (VALUE >= 0 AND VALUE <= 32767);
  END IF;
END $$;

-- Users
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  create_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_login_time TIMESTAMPTZ
);

-- Knowledge Dimension
CREATE TABLE IF NOT EXISTS knowledge_dimension (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  description VARCHAR(200)
);

-- Question
-- question_type: 1=short_answer, 2=lesson_design
-- difficulty: 1=easy, 2=medium, 3=hard
CREATE TABLE IF NOT EXISTS question (
  id BIGSERIAL PRIMARY KEY,
  question_type INT NOT NULL CHECK (question_type IN (1,2)),
  difficulty INT NOT NULL CHECK (difficulty IN (1,2,3)),
  title TEXT NOT NULL,
  material TEXT,
  requirements VARCHAR(500),
  score small_posint NOT NULL DEFAULT 10,
  suggest_time small_posint,
  word_limit small_posint,
  knowledge_ids JSONB,
  score_points JSONB,
  create_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  answer_content TEXT,
  scoring_criteria TEXT
);

-- Relation: question <-> knowledge_dimension
CREATE TABLE IF NOT EXISTS question_kd_relation (
  q_id BIGINT NOT NULL REFERENCES question(id) ON DELETE CASCADE,
  kd_id BIGINT NOT NULL REFERENCES knowledge_dimension(id) ON DELETE RESTRICT,
  PRIMARY KEY (q_id, kd_id)
);

-- Answer Record
-- answer_type: 1=text, 2=file, 3=auto
CREATE TABLE IF NOT EXISTS answer_record (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  q_id BIGINT NOT NULL REFERENCES question(id) ON DELETE CASCADE,
  answer_type INT NOT NULL DEFAULT 1 CHECK (answer_type IN (1,2,3)),
  original_answer TEXT,
  submit_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  total_score DECIMAL(5,2),
  subitem_scores JSONB,
  dimension_scores JSONB,
  comments TEXT,
  hit_score_points JSONB
);

-- Constraints (idempotent)
ALTER TABLE question
  ADD CONSTRAINT IF NOT EXISTS question_score_nonneg CHECK (score >= 0);

ALTER TABLE answer_record
  ADD CONSTRAINT IF NOT EXISTS total_score_nonneg CHECK (total_score IS NULL OR total_score >= 0);

-- Indexes (idempotent)
CREATE INDEX IF NOT EXISTS idx_question_created_at ON question (create_time DESC);
CREATE INDEX IF NOT EXISTS idx_question_type ON question (question_type, difficulty);
CREATE INDEX IF NOT EXISTS idx_question_scorepoints_gin ON question USING GIN (score_points);
CREATE INDEX IF NOT EXISTS idx_answer_record_user ON answer_record (user_id, submit_time DESC);
CREATE INDEX IF NOT EXISTS idx_answer_record_qid ON answer_record (q_id, submit_time DESC);
CREATE INDEX IF NOT EXISTS idx_answer_record_dim_scores_gin ON answer_record USING GIN (dimension_scores);
CREATE INDEX IF NOT EXISTS idx_qkd_kd ON question_kd_relation (kd_id);
