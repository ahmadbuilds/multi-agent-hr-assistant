/** 
* USERS
* Note: This table contains user data. Users should only be able to view and update their own data.
*/
create table if not exists public.users (
  id uuid references auth.users on delete cascade not null primary key,
  username text unique,
  full_name text,
  avatar_url text,
  email text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  
  constraint username_length check (char_length(username) >= 3)
);

alter table public.users enable row level security;

create policy "Users can view their own profile." on public.users
  for select using (auth.uid() = id);

create policy "Users can update their own profile." on public.users
  for update using (auth.uid() = id);

/** 
* LEAVE BALANCE
*/
create table if not exists public.leave_balance (
  user_id uuid references public.users(id) on delete cascade not null primary key,
  balance int default 0,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.leave_balance enable row level security;

create policy "Users can view their own leave balance." on public.leave_balance
  for select using (auth.uid() = user_id);

create policy "Admins can view all leave balances." on public.leave_balance
  for select using (auth.jwt() ->> 'email' = 'crisitiano678@gmail.com');

create policy "Admins can update all leave balances." on public.leave_balance
  for update using (auth.jwt() ->> 'email' = 'crisitiano678@gmail.com');

/**
* TICKETS
*/
create table if not exists public.tickets (
  ticket_id uuid default gen_random_uuid() primary key,
  user_id uuid references public.users(id) on delete cascade not null,
  ticket_type text check (ticket_type in ('complaint', 'help', 'leave')),
  subject text,
  description text,
  status text check (status in ('in_progress', 'accepted', 'rejected')) default 'in_progress',
  leave_days int, -- Optional: used if ticket_type is 'leave'
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.tickets enable row level security;

create policy "Users can view their own tickets." on public.tickets
  for select using (auth.uid() = user_id);

create policy "Users can create tickets." on public.tickets
  for insert with check (auth.uid() = user_id);

create policy "Admins can view all tickets." on public.tickets
  for select using (auth.jwt() ->> 'email' = 'crisitiano678@gmail.com');

create policy "Admins can update tickets." on public.tickets
  for update using (auth.jwt() ->> 'email' = 'crisitiano678@gmail.com');


-- Handle User Creation
create or replace function public.handle_new_user() 
returns trigger as $$
begin
  insert into public.users (id, username, full_name, avatar_url, email)
  values (new.id, new.raw_user_meta_data->>'username', new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'avatar_url', new.email);
  
  -- Initialize leave balance for new user
  insert into public.leave_balance (user_id, balance)
  values (new.id, 10);
  
  return new;
end;
$$ language plpgsql security definer;

-- Trigger to create user profile on signup
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Handle Ticket Updates (Leave Balance Logic)
create or replace function public.handle_ticket_update()
returns trigger as $$
begin
  -- Check if status changed to 'accepted' and it is a 'leave' ticket
  if old.status <> 'accepted' and new.status = 'accepted' and new.ticket_type = 'leave' then
    update public.leave_balance
    set balance = balance - coalesce(new.leave_days, 0)
    where user_id = new.user_id;
  end if;
  return new;
end;
$$ language plpgsql security definer;

-- Trigger for ticket updates
drop trigger if exists on_ticket_updated on public.tickets;
create trigger on_ticket_updated
  after update on public.tickets
  for each row execute procedure public.handle_ticket_update();

/**
* CHATS
*/
create table if not exists public.chats (
  chat_id uuid default gen_random_uuid() primary key,
  user_id uuid references public.users(id) on delete cascade not null,
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
  uploaded_by uuid references auth.users on delete cascade
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
  on storage.objects
  for select
  using ( bucket_id = 'avatars' );

-- Anyone can upload avatars
create policy "Anyone can upload avatar images."
  on storage.objects
  for insert
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
