-- Axioma initial schema, RLS policies, atomic quota RPC, and private Storage bucket

create extension if not exists pgcrypto;

create schema if not exists private;

-- 1. Profiles
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text,
  full_name text,
  plan_tier text not null default 'free' check (plan_tier in ('free', 'pro')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "Users can view own profile"
  on public.profiles
  for select
  to authenticated
  using ((select auth.uid()) = id);

create policy "Users can update own profile"
  on public.profiles
  for update
  to authenticated
  using ((select auth.uid()) = id)
  with check ((select auth.uid()) = id);

create or replace function private.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create or replace trigger profiles_set_updated_at
  before update on public.profiles
  for each row
  execute function private.set_updated_at();

create or replace function private.protect_plan_tier()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.plan_tier is distinct from old.plan_tier then
    if current_user not in ('postgres', 'supabase_admin', 'service_role')
       and coalesce(current_setting('request.jwt.claim.role', true), '') <> 'service_role' then
      raise exception 'plan_tier cannot be modified by client';
    end if;
  end if;
  return new;
end;
$$;

create or replace trigger profiles_protect_plan_tier
  before update on public.profiles
  for each row
  execute function private.protect_plan_tier();

create or replace function private.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id, email, full_name, plan_tier)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data ->> 'full_name', ''),
    'free'
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

create or replace trigger on_auth_user_created
  after insert on auth.users
  for each row
  execute function private.handle_new_user();

-- 2. Problems history
create table if not exists public.problems (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  subject text not null check (subject in ('math', 'physics', 'chemistry', 'engineering')),
  input_type text not null check (input_type in ('text', 'latex', 'image')),
  raw_input text,
  image_path text,
  verified_result_latex text,
  solution_summary text,
  steps_json jsonb not null default '[]'::jsonb,
  plot_data jsonb,
  engine_metadata jsonb not null default '{}'::jsonb,
  is_favorite boolean not null default false,
  created_at timestamptz not null default now()
);

create index if not exists idx_problems_user_created
  on public.problems (user_id, created_at desc);

create index if not exists idx_problems_user_favorites
  on public.problems (user_id, created_at desc)
  where is_favorite = true;

alter table public.problems enable row level security;

create policy "Users can view own problems"
  on public.problems
  for select
  to authenticated
  using ((select auth.uid()) = user_id);

create policy "Users can insert own problems"
  on public.problems
  for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

create policy "Users can update own problems"
  on public.problems
  for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

create policy "Users can delete own problems"
  on public.problems
  for delete
  to authenticated
  using ((select auth.uid()) = user_id);

-- 3. Daily usage (freemium quota tracking)
create table if not exists public.daily_usage (
  user_id uuid not null references auth.users (id) on delete cascade,
  usage_date date not null default current_date,
  solve_count integer not null default 0 check (solve_count >= 0),
  updated_at timestamptz not null default now(),
  primary key (user_id, usage_date)
);

alter table public.daily_usage enable row level security;

create policy "Users can view own daily usage"
  on public.daily_usage
  for select
  to authenticated
  using ((select auth.uid()) = user_id);

create or replace function public.consume_daily_solve(p_user_id uuid, p_limit integer)
returns table (allowed boolean, current_count integer, remaining integer)
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_count integer;
begin
  insert into public.daily_usage (user_id, usage_date, solve_count, updated_at)
  values (p_user_id, current_date, 0, now())
  on conflict (user_id, usage_date) do nothing;

  select du.solve_count
  into v_count
  from public.daily_usage du
  where du.user_id = p_user_id
    and du.usage_date = current_date
  for update;

  if v_count >= p_limit then
    return query select false, v_count, 0;
    return;
  end if;

  update public.daily_usage
  set solve_count = solve_count + 1,
      updated_at = now()
  where user_id = p_user_id
    and usage_date = current_date
  returning solve_count into v_count;

  return query select true, v_count, greatest(p_limit - v_count, 0);
end;
$$;

revoke all on function public.consume_daily_solve(uuid, integer) from public, anon, authenticated;
grant execute on function public.consume_daily_solve(uuid, integer) to service_role;

create or replace function public.refund_daily_solve(p_user_id uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  update public.daily_usage
  set solve_count = greatest(solve_count - 1, 0),
      updated_at = now()
  where user_id = p_user_id
    and usage_date = current_date;
end;
$$;

revoke all on function public.refund_daily_solve(uuid) from public, anon, authenticated;
grant execute on function public.refund_daily_solve(uuid) to service_role;

-- 4. Subscriptions (for RevenueCat / Stripe webhooks)
create table if not exists public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  provider text not null check (provider in ('revenuecat', 'stripe')),
  status text not null,
  current_period_end timestamptz,
  external_customer_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_subscriptions_user_id
  on public.subscriptions (user_id);

alter table public.subscriptions enable row level security;

create policy "Users can view own subscriptions"
  on public.subscriptions
  for select
  to authenticated
  using ((select auth.uid()) = user_id);

create or replace trigger subscriptions_set_updated_at
  before update on public.subscriptions
  for each row
  execute function private.set_updated_at();

-- 5. Storage bucket for problem images (private, per-user folder)
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'problem-images',
  'problem-images',
  false,
  10485760,
  array['image/jpeg', 'image/png', 'image/webp']
)
on conflict (id) do nothing;

create policy "Users can view own problem images"
  on storage.objects
  for select
  to authenticated
  using (
    bucket_id = 'problem-images'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

create policy "Users can upload own problem images"
  on storage.objects
  for insert
  to authenticated
  with check (
    bucket_id = 'problem-images'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

create policy "Users can update own problem images"
  on storage.objects
  for update
  to authenticated
  using (
    bucket_id = 'problem-images'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  )
  with check (
    bucket_id = 'problem-images'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

create policy "Users can delete own problem images"
  on storage.objects
  for delete
  to authenticated
  using (
    bucket_id = 'problem-images'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );
