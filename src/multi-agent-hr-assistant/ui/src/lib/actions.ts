"use server"

import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { cookies } from 'next/headers'

// Helper to create server client
async function createClient() {
  const cookieStore = await cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
        set(name: string, value: string, options: CookieOptions) {
          try {
            cookieStore.set({ name, value, ...options })
          } catch (error) {
            // The `set` method was called from a Server Component.
            // This can be ignored if you have middleware refreshing
            // user sessions.
          }
        },
        remove(name: string, options: CookieOptions) {
          try {
            cookieStore.set({ name, value: '', ...options })
          } catch (error) {
            // The `delete` method was called from a Server Component.
            // This can be ignored if you have middleware refreshing
            // user sessions.
          }
        },
      },
    }
  )
}

export async function getChats(offset: number = 0, limit: number = 20) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return []

  const { data, error } = await supabase
    .from('chats')
    .select('*')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) console.error("Error fetching chats:", error)
  return data || []
}

import { revalidatePath } from 'next/cache'

// ... imports

export async function createChat(firstMessage: string, attachmentUrl?: string, attachmentName?: string) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error("Unauthorized")

  // Create Chat
  const title = firstMessage.slice(0, 30) + (firstMessage.length > 30 ? '...' : '')
  const { data: chat, error: chatError } = await supabase
    .from('chats')
    .insert({ user_id: user.id, title })
    .select()
    .single()

  if (chatError) throw chatError

  // Add Message
  await supabase.from('messages').insert({
    chat_id: chat.chat_id,
    content: firstMessage,
    type: 'user',
    attachment_url: attachmentUrl,
    attachment_name: attachmentName
  })

  revalidatePath('/dashboard')
  return chat
}

export async function sendMessage(chatId: string, content: string, type: 'user' | 'ai' = 'user', attachmentUrl?: string, attachmentName?: string) {
  const supabase = await createClient()
  const { error } = await supabase.from('messages').insert({
    chat_id: chatId,
    content,
    type,
    attachment_url: attachmentUrl,
    attachment_name: attachmentName
  })
  if (error) throw error
  revalidatePath(`/dashboard/chat/${chatId}`)
}

export async function getMessages(chatId: string) {
  const supabase = await createClient()
  const { data, error } = await supabase
    .from('messages')
    .select('*')
    .eq('chat_id', chatId)
    .order('created_at', { ascending: true })

  if (error) throw error
  return data || []
}

export async function getUserProfile() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return null

  const { data } = await supabase
    .from('users')
    .select('*')
    .eq('id', user.id)
    .single()
  
  return data
}

export async function uploadDocument(formData: FormData) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) {
    throw new Error("Unauthorized")
  }

  const file = formData.get('file') as File
  if (!file) throw new Error("No file content")

  const fileName = `${Date.now()}_${file.name}`
  const { error: uploadError } = await supabase.storage
    .from('Policy Documents')
    .upload(fileName, file)

  if (uploadError) throw uploadError

  const { data: { publicUrl } } = supabase.storage
    .from('Policy Documents')
    .getPublicUrl(fileName)

  // Insert into documents table
  const { error: dbError } = await supabase.from('documents').insert({
    document_url: publicUrl,
    document_name: file.name,
    uploaded_by: user.id
  })

  if (dbError) throw dbError
  return { success: true, publicUrl, fileName: file.name }
}
