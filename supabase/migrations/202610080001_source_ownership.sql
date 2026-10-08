-- Preparatory schema only. Ingestion/quota/delete APIs are not enabled yet.
begin;

create table public.sources (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete restrict,
  kind text not null check (kind in ('file', 'bookmark')),
  title text not null check (length(btrim(title)) between 1 and 500),
  notes text not null default '' check (length(notes) <= 16000),
  original_url text,
  created_at timestamptz not null default now(),
  deleted_at timestamptz,
  unique (id, owner_id),
  check ((kind = 'bookmark' and original_url is not null
    and length(original_url) <= 8192 and original_url ~ '^https?://')
    or (kind = 'file' and original_url is null))
);
comment on column public.sources.original_url is
  'Untrusted provenance only. This constraint does not authorize a network fetch.';

create table public.source_versions (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null,
  owner_id uuid not null,
  content_sha256 text not null check (content_sha256 ~ '^[0-9a-f]{64}$'),
  parser_version text not null check (length(parser_version) between 1 and 200),
  created_at timestamptz not null default now(),
  foreign key (source_id, owner_id) references public.sources(id, owner_id)
    on delete restrict
);
create index sources_owner_visible on public.sources(owner_id, created_at desc)
  where deleted_at is null;
create index source_versions_source_owner on public.source_versions(source_id, owner_id);

alter table public.sources enable row level security;
alter table public.sources force row level security;
alter table public.source_versions enable row level security;
alter table public.source_versions force row level security;

-- Explicit revocation also handles Supabase's default public-schema grants.
revoke all on public.sources, public.source_versions from public, anon, authenticated;
grant select on public.sources, public.source_versions to authenticated;
grant update (title, notes) on public.sources to authenticated;

create policy source_read on public.sources for select to authenticated
  using (owner_id = (select auth.uid()) and deleted_at is null);
create policy source_edit on public.sources for update to authenticated
  using (owner_id = (select auth.uid()) and deleted_at is null)
  with check (owner_id = (select auth.uid()) and deleted_at is null);
create policy version_read on public.source_versions for select to authenticated
  using (owner_id = (select auth.uid()) and exists (
    select 1 from public.sources s
    where s.id = source_id and s.owner_id = source_versions.owner_id
      and s.deleted_at is null
  ));

-- No client INSERT/DELETE or worker grants: quota, publication and cleanup
-- transitions need dedicated, reviewed APIs before they can be enabled.
commit;
