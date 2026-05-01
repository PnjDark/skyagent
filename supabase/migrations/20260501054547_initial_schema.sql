-- Layer A: Supabase Schema

create table if not exists projects (
  id text primary key,
  tier text not null,
  status text not null,
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

create table if not exists github_events (
  id bigserial primary key,
  repo text not null,
  event_type text not null,
  payload jsonb,
  importance text,
  points int default 0,
  processed_at timestamptz default now()
);

create table if not exists daily_priorities (
  id bigserial primary key,
  date date not null unique,
  content text not null,
  priorities jsonb,
  generated_at timestamptz default now()
);

create table if not exists project_logs (
  id bigserial primary key,
  date date not null,
  project_id text references projects(id),
  achievement text not null,
  logged_at timestamptz default now()
);

create table if not exists content_drafts (
  id bigserial primary key,
  project_id text references projects(id),
  github_event_id bigint references github_events(id),
  linkedin_draft text,
  x_draft text,
  portfolio_update text,
  status text default 'pending',
  buffer_post_ids jsonb,
  created_at timestamptz default now(),
  approved_at timestamptz
);

create table if not exists portfolio_feed (
  id bigserial primary key,
  project_id text references projects(id),
  event_type text,
  summary text,
  date date,
  type text,
  github_event_id bigint references github_events(id),
  created_at timestamptz default now()
);

create or replace function update_updated_at()
returns trigger as $$
begin new.updated_at = now(); return new; end;
$$ language plpgsql;

drop trigger if exists projects_updated_at on projects;
create trigger projects_updated_at
  before update on projects
  for each row execute function update_updated_at();

create index if not exists github_events_repo_idx on github_events(repo);
create index if not exists github_events_processed_at_idx on github_events(processed_at desc);
create index if not exists content_drafts_status_idx on content_drafts(status);
create index if not exists portfolio_feed_date_idx on portfolio_feed(date desc);
create index if not exists project_logs_project_id_date_idx on project_logs(project_id, date desc);
