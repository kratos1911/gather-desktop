-- Disposable integration database only. Roles mirror Supabase's API boundary.
-- Trust transport is confined to the private test Docker network, no DB host port.
create role anon nologin;
create role authenticated nologin;
create role service_role nologin bypassrls;
create role authenticator login noinherit;
grant anon, authenticated, service_role to authenticator;
create role supabase_auth_admin login createrole;
create role supabase_storage_admin login createrole bypassrls;
grant anon, authenticated, service_role to supabase_storage_admin;
create schema auth authorization supabase_auth_admin;
alter role supabase_auth_admin set search_path = auth, public;
create schema storage authorization supabase_storage_admin;
grant usage on schema storage to anon, authenticated, service_role;
alter default privileges for role supabase_storage_admin in schema storage
  grant all on tables to anon, authenticated, service_role;
alter default privileges for role supabase_storage_admin in schema storage
  grant all on sequences to anon, authenticated, service_role;
grant usage on schema public to anon, authenticated, service_role;
grant create on schema public to supabase_storage_admin;
grant all on database postgres to supabase_auth_admin, supabase_storage_admin;
-- Auth owns and installs its real users tables and auth.uid() migrations.
grant usage on schema auth to anon,authenticated,service_role;
alter default privileges for role postgres in schema public grant all on tables to service_role;
