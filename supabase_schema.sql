-- たびログ Supabase スキーマ
-- Supabase ダッシュボード → SQL Editor に全文貼り付けて Run してください

create table if not exists users (
  id text primary key,
  name text not null,
  salt text not null,
  pw text not null,
  avatar_url text,
  default_visibility text not null default 'friends',
  lang text not null default 'ja',
  created_at timestamptz default now()
);

create table if not exists trips (
  id uuid primary key,
  owner text not null references users(id) on delete cascade,
  place text not null,
  country text not null,
  city text not null,
  lat double precision not null,
  lon double precision not null,
  visit_date date not null,
  expectation text not null,
  reality text not null default '',
  rating int not null default 0,
  photo_rating int not null default 0,
  gap text,
  status text not null default 'planned',
  visibility text not null default 'default',
  capsule boolean not null default false,
  companions jsonb not null default '[]',
  reactions jsonb not null default '{}',
  photo_urls jsonb not null default '[]',
  created_at timestamptz default now()
);
create index if not exists trips_owner_idx on trips(owner);

create table if not exists friendships (
  user_a text not null references users(id) on delete cascade,
  user_b text not null references users(id) on delete cascade,
  primary key (user_a, user_b)
);

create table if not exists friend_requests (
  from_user text not null references users(id) on delete cascade,
  to_user text not null references users(id) on delete cascade,
  primary key (from_user, to_user)
);

create table if not exists suggestions (
  id uuid primary key,
  from_user text not null references users(id) on delete cascade,
  to_user text not null references users(id) on delete cascade,
  place text not null,
  country text not null,
  city text not null,
  lat double precision not null,
  lon double precision not null,
  note text not null default '',
  created_at timestamptz default now()
);

-- 写真用の公開バケット
insert into storage.buckets (id, name, public)
values ('photos', 'photos', true)
on conflict (id) do nothing;

-- バケットへのアップロード/上書きを許可
create policy "photos anon insert" on storage.objects
  for insert to anon with check (bucket_id = 'photos');
create policy "photos anon update" on storage.objects
  for update to anon using (bucket_id = 'photos');
