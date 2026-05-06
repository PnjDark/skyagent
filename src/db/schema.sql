-- Sky Agent Schema
-- Run this in Neon SQL editor or via: psql $DATABASE_URL -f src/db/schema.sql

-- Projects (auto-discovered from GitHub webhooks)
CREATE TABLE IF NOT EXISTS projects (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_name     TEXT NOT NULL UNIQUE,
  github_url    TEXT NOT NULL,
  description   TEXT DEFAULT '',
  momentum_score FLOAT DEFAULT 0,
  last_push     TIMESTAMPTZ,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Every GitHub event becomes a row here
CREATE TABLE IF NOT EXISTS activities (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  event_type  TEXT NOT NULL,
  event_data  JSONB NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Merged PRs, releases, milestones
CREATE TABLE IF NOT EXISTS wins (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  win_type    TEXT NOT NULL, -- 'release' | 'merge'
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Daily focus (top 3 projects per day)
CREATE TABLE IF NOT EXISTS daily_focus (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date        DATE NOT NULL UNIQUE,
  priorities  JSONB NOT NULL DEFAULT '[]',
  mode        TEXT NOT NULL DEFAULT 'normal',
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Content drafts (AI-generated posts awaiting approval)
CREATE TABLE IF NOT EXISTS content_drafts (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  activity_id UUID REFERENCES activities(id) ON DELETE SET NULL,
  project_id  UUID REFERENCES projects(id) ON DELETE CASCADE,
  platform    TEXT NOT NULL, -- 'linkedin' | 'twitter'
  content     TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'draft', -- 'draft' | 'approved' | 'published'
  approved_at TIMESTAMPTZ,
  published_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-update updated_at on projects
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS projects_updated_at ON projects;
CREATE TRIGGER projects_updated_at
  BEFORE UPDATE ON projects
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Indexes
CREATE INDEX IF NOT EXISTS activities_project_id_idx ON activities(project_id);
CREATE INDEX IF NOT EXISTS activities_created_at_idx ON activities(created_at DESC);
CREATE INDEX IF NOT EXISTS wins_project_id_idx ON wins(project_id);
CREATE INDEX IF NOT EXISTS wins_created_at_idx ON wins(created_at DESC);
CREATE INDEX IF NOT EXISTS content_drafts_status_idx ON content_drafts(status);
CREATE INDEX IF NOT EXISTS daily_focus_date_idx ON daily_focus(date DESC);
