begin;
-- Configuration only: objects must be created/deleted through the Storage API.
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('gather-originals','gather-originals',false,65536,array['text/plain','text/markdown']);

-- First slice: authenticated reads of an exact server-assigned original key.
-- No client upload/update/delete policy; trusted ingestion is still deferred.
create policy gather_original_read on storage.objects for select to authenticated
using (bucket_id='gather-originals' and exists (
  select 1 from public.sources s
  where s.owner_id=(select auth.uid()) and s.deleted_at is null and s.kind='file'
    and name=s.owner_id::text || '/' || s.id::text || '/original'
));

create or replace function gather_private.finish_source_cleanup(p_source_id uuid) returns boolean
language plpgsql security definer set search_path = '' as $$
declare v_owner uuid; v_accounted boolean;
begin
  select owner_id into v_owner from gather_private.cleanup_requests where source_id=p_source_id;
  if not found then return false; end if;
  perform 1 from gather_private.source_quotas where owner_id=v_owner for update;
  perform 1 from public.sources where id=p_source_id and owner_id=v_owner and deleted_at is not null for update;
  if not found then return false; end if;
  -- A failed/missed Storage API deletion must retain the tombstone, queue and quota.
  -- Metadata absence is necessary, not proof against in-flight privileged uploads.
  -- Production ingestion must fence uploads before invoking this finalizer.
  if exists(select 1 from storage.objects where bucket_id='gather-originals'
    and starts_with(name,v_owner::text || '/' || p_source_id::text || '/')) then
    raise exception 'storage_cleanup_pending' using errcode='P0001';
  end if;
  select exists(select 1 from gather_private.save_receipts where source_id=p_source_id and owner_id=v_owner) into v_accounted;
  delete from public.source_versions where source_id=p_source_id and owner_id=v_owner;
  delete from gather_private.cleanup_requests where source_id=p_source_id and owner_id=v_owner;
  delete from public.sources where id=p_source_id and owner_id=v_owner;
  if v_accounted then update gather_private.source_quotas set used=used-1 where owner_id=v_owner; end if;
  return true;
end $$;
revoke all on function gather_private.finish_source_cleanup(uuid) from public, anon, authenticated;
commit;
