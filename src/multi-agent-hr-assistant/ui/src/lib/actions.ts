"use server"

import { revalidatePath } from 'next/cache'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

async function createClient() {
  const cookieStore = await cookies()

  const cookieMap = new Map(
    cookieStore.getAll().map((c) => [c.name, c.value])
  )

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return Array.from(cookieMap, ([name, value]) => ({ name, value }))
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) => {
              cookieMap.set(name, value)
              cookieStore.set(name, value, options)
            })
          } catch {
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

  if (chatError) throw new Error(chatError.message)
  revalidatePath('/dashboard')
  return chat
}

export async function sendMessage(chatId: string, content: string, type: 'user' | 'ai' = 'user', attachmentUrl?: string, attachmentName?: string) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error("Unauthorized")
  const { error } = await supabase.from('messages').insert({
    chat_id: chatId,
    content,
    type,
    attachment_url: attachmentUrl,
    attachment_name: attachmentName
  })
  if (error) throw new Error(error.message)
  revalidatePath(`/dashboard/chat/${chatId}`)
}

export async function getMessages(chatId: string) {
  const supabase = await createClient()
  await supabase.auth.getUser()
  const { data, error } = await supabase
    .from('messages')
    .select('*')
    .eq('chat_id', chatId)
    .order('created_at', { ascending: true })

  if (error) throw new Error(error.message)
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

export async function uploadDocument(formData: FormData): Promise<{ success: boolean; publicUrl: string; fileName: string; extractedText: string }> {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) {
    throw new Error("Unauthorized")
  }

  const file = formData.get('file') as File
  if (!file) throw new Error("No file provided")

  const fileName = `${Date.now()}_${file.name}`
  const { error: uploadError } = await supabase.storage
    .from('Policy Documents')
    .upload(fileName, file)

  if (uploadError) throw uploadError

  const { data: { publicUrl } } = supabase.storage
    .from('Policy Documents')
    .getPublicUrl(fileName)

  // Extract text content from the uploaded file
  let extractedText = ''
  try {
    const arrayBuffer = await file.arrayBuffer()
    const buffer = Buffer.from(arrayBuffer)
    const ext = file.name.split('.').pop()?.toLowerCase()

    if (ext === 'pdf') {
      const { PDFParse } = await import('pdf-parse')
      const parser = new PDFParse({ data: buffer })
      const data = await parser.getText()
      extractedText = data.text
      await parser.destroy()
    } else if (ext === 'docx' || ext === 'doc') {
      const mammoth = await import('mammoth')
      const result = await mammoth.extractRawText({ buffer })
      extractedText = result.value
    }
  } catch (extractError) {
    console.error('Error extracting text from document:', extractError)
  }

  return { success: true, publicUrl, fileName: file.name, extractedText }
}
