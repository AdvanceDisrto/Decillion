-- Run only after Supabase BUDDY project is active and backup is confirmed.
create table if not exists public.i_receipts (
  id text primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  receipt jsonb not null,
  created_at timestamptz not null default now()
);
create index if not exists i_receipts_user_time on public.i_receipts(user_id,created_at desc);
alter table public.i_receipts enable row level security;
revoke all on public.i_receipts from anon;
grant select, insert on public.i_receipts to authenticated;
create policy "read own receipts" on public.i_receipts for select to authenticated using ((select auth.uid())=user_id);
create policy "insert own receipts" on public.i_receipts for insert to authenticated with check ((select auth.uid())=user_id);
-- No update/delete policies: append-only from browser role.
