/** 
* USERS
* Note: This table contains user data. Users should only be able to view and update their own data.
*/
create table if not exists public.users (
  id uuid references auth.users not null primary key,
  username text unique,
  full_name text,
  avatar_url text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  
  constraint username_length check (char_length(username) >= 3)
);

alter table public.users enable row level security;

create policy "Users can view their own profile." on public.users
  for select using (auth.uid() = id);

create policy "Users can update their own profile." on public.users
  for update using (auth.uid() = id);

-- Handle User Creation
create or replace function public.handle_new_user() 
returns trigger as $$
begin
  insert into public.users (id, username, full_name, avatar_url)
  values (new.id, new.raw_user_meta_data->>'username', new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'avatar_url');
  return new;
end;
$$ language plpgsql security definer;

-- Trigger to create user profile on signup
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

/**
* CHATS
*/
create table if not exists public.chats (
  chat_id uuid default gen_random_uuid() primary key,
  user_id uuid references public.users(id) not null,
  title text default 'New Chat',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.chats enable row level security;

create policy "Users can view their own chats." on public.chats
  for select using (auth.uid() = user_id);

create policy "Users can create their own chats." on public.chats
  for insert with check (auth.uid() = user_id);

create policy "Users can delete their own chats." on public.chats
  for delete using (auth.uid() = user_id);

/**
* MESSAGES
*/
create table if not exists public.messages (
  id uuid default gen_random_uuid() primary key,
  chat_id uuid references public.chats(chat_id) on delete cascade not null,
  content text,
  attachment_url text,
  attachment_name text,
  type text check (type in ('user', 'ai')),
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.messages enable row level security;

create policy "Users can view messages in their chats." on public.messages
  for select using (
    exists ( select 1 from public.chats where chat_id = messages.chat_id and user_id = auth.uid() )
  );

create policy "Users can insert messages in their chats." on public.messages
  for insert with check (
    exists ( select 1 from public.chats where chat_id = messages.chat_id and user_id = auth.uid() )
  );

/**
* DOCUMENTS
*/
create table if not exists public.documents (
  document_id uuid default gen_random_uuid() primary key,
  document_url text not null,
  document_name text not null,
  vector_stored boolean default false,
  uploaded_at timestamp with time zone default timezone('utc'::text, now()) not null,
  uploaded_by uuid references auth.users
);

alter table public.documents enable row level security;

create policy "Anyone can view documents." on public.documents
  for select using (auth.role() = 'authenticated');

-- Only admin (crisitiano678@gmail.com) can insert documents
create policy "Only admin can insert documents." on public.documents
  for insert with check (auth.jwt() ->> 'email' = 'crisitiano678@gmail.com');

/**
* STORAGE POLICIES
*/

-- Avatars
create policy "Avatar images are publicly accessible."
  on storage.objects for select
  using ( bucket_id = 'avatars' );

  on storage.objects for insert
  with check ( bucket_id = 'avatars' );

create policy "Anyone can delete their own avatar."
  on storage.objects for delete
  using ( bucket_id = 'avatars' and auth.uid() = owner );

-- Ensure Bucket Exists
insert into storage.buckets (id, name, public)
values ('Policy Documents', 'Policy Documents', true)
on conflict (id) do nothing;

create policy "Documents are accessible by authenticated users."
  on storage.objects for select
  using ( bucket_id = 'Policy Documents' and auth.role() = 'authenticated' );

create policy "Only admin can upload policy documents."
  on storage.objects for insert
  with check ( bucket_id = 'Policy Documents' and auth.jwt() ->> 'email' = 'crisitiano678@gmail.com' );
