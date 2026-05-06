-- Layer A: Supabase Schema
-- Run this in Supabase SQL editor

create table projects (
  id text primary key,                        -- e.g. "SpecNest"
  tier text not null,                         -- S/A/B/C/D
  status text not null,                       -- active/paused/danger_zone/archived/killed/ready/design/maintaining/experimental
  category text,
  revenue_potential text,
  completion int default 0,
  last_activity date,
  deadline date,
  priority_boost int default 0,
  description text,
  next_milestone text,
  github_repo text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table github_events (
  id bigserial primary key,
  repo text not null,                         -- e.g. "penjy/specnest"
  event_type text not null,                   -- push/release/pr_merged/pr_opened/star/fork/issue_closed/repo_created/repo_publicized
  payload jsonb,
  importance text,                            -- high/medium/low
  points int default 0,
  processed_at timestamptz default now()
);

create table daily_priorities (
  id bigserial primary key,
  date date not null unique,
  content text not null,                      -- TODAY.md content
  priorities jsonb,                           -- [{name, score, tier}]
  generated_at timestamptz default now()
);

create table project_logs (
  id bigserial primary key,
  date date not null,
  project_id text references projects(id),
  achievement text not null,
  logged_at timestamptz default now()
);

create table content_drafts (
  id bigserial primary key,
  project_id text references projects(id),
  github_event_id bigint references github_events(id),
  linkedin_draft text,
  x_draft text,
  portfolio_update text,
  status text default 'pending',              -- pending/approved/rejected/scheduled
  buffer_post_ids jsonb,                      -- {linkedin: id, twitter: id}
  created_at timestamptz default now(),
  approved_at timestamptz
);

create table portfolio_feed (
  id bigserial primary key,
  project_id text references projects(id),
  event_type text,
  summary text,
  date date,
  type text,                                  -- launch/community/update/milestone
  github_event_id bigint references github_events(id),
  created_at timestamptz default now()
);

-- Auto-update updated_at on projects
create or replace function update_updated_at()
returns trigger as $$
begin new.updated_at = now(); return new; end;
$$ language plpgsql;

create trigger projects_updated_at
  before update on projects
  for each row execute function update_updated_at();

-- Indexes for common queries
create index on github_events(repo);
create index on github_events(processed_at desc);
create index on content_drafts(status);
create index on portfolio_feed(date desc);
create index on project_logs(project_id, date desc);
