-- Run in Supabase SQL editor only if you already ran schema.sql before Phase 4
alter table content_drafts add column if not exists buffer_post_ids jsonb;
