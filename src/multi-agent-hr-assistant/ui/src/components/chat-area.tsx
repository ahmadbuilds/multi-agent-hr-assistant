"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Paperclip, ArrowUp, X, FileText } from "lucide-react"
import { toast } from "sonner"
import { createChat, sendMessage, uploadDocument } from "@/lib/actions"
import { cn } from "@/lib/utils"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import { Header } from "@/components/header"

interface Message {
  id: number | string
  content: string
  type: 'user' | 'ai'
  attachment_url?: string
  attachment_name?: string
  created_at?: string
}

interface ChatAreaProps {
  chatId?: string
  initialMessages?: Message[]
}

export function ChatArea({ chatId, initialMessages = [] }: ChatAreaProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [isAdmin, setIsAdmin] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      if (data.user?.email === 'crisitiano678@gmail.com') {
        setIsAdmin(true)
      }
    })
  }, [])

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
        setSelectedFile(e.target.files[0])
    }
    // Reset input so same file can be selected again
    e.target.value = ""
  }

  const handleSend = async () => {
    if ((!input.trim() && !selectedFile) || loading) return

    const currentInput = input
    const currentFile = selectedFile
    const tempId = Date.now()

    // Optimistic UI Update
    const optimisticMsg: Message = { 
        id: tempId, 
        content: currentInput, 
        type: 'user',
        attachment_name: currentFile?.name,
        created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, optimisticMsg])
    
    setInput("")
    setSelectedFile(null)
    setLoading(true)

    let activeChatId = chatId
    let uploadedDocUrl: string | undefined
    let uploadedDocName: string | undefined

    // 1. Upload File if present
    if (currentFile) {
        const formData = new FormData()
        formData.append('file', currentFile)
        
        try {
            const result = await uploadDocument(formData)
            uploadedDocUrl = result.publicUrl
            uploadedDocName = result.fileName
        } catch (err) {
            console.error("Upload failed", err)
            toast.error(`Failed to upload ${currentFile.name}`, {
                description: "Please check your connection and try again."
            })
        }
    }

    try {
        // 2. Create Chat OR Send Message
        if (!activeChatId) {
            const newChat = await createChat(currentInput, uploadedDocUrl, uploadedDocName)
            activeChatId = newChat.chat_id
            router.refresh()
            router.push(`/dashboard/chat/${activeChatId}`)
        } else {
            await sendMessage(activeChatId, currentInput, 'user', uploadedDocUrl, uploadedDocName)
            router.refresh() 
        }

        // 3. AI Response (Placeholder)
        setTimeout(() => {
            const aiMsg: Message = { 
                id: Date.now() + 2, 
                content: "This is a simulated AI response.", 
                type: 'ai', 
                created_at: new Date().toISOString() 
            }
            setMessages(prev => [...prev, aiMsg])
            if (activeChatId) {
                sendMessage(activeChatId, "This is a simulated AI response.", 'ai')
            }
        }, 1000)
        
    } catch (error) {
        console.error(error)
        toast.error("Failed to send message")
    } finally {
        setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full max-h-screen">
      <Header />
      
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-muted/10 scrollbar-track-transparent">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-muted-foreground opacity-50 space-y-4">
             <div className="h-16 w-16 bg-primary/10 rounded-full flex items-center justify-center">
                 <span className="text-3xl">🤖</span>
             </div>
             <h2 className="text-2xl font-semibold">How can I help you today?</h2>
          </div>
        )}
        <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg) => (
            <div
                key={msg.id}
                className={cn(
                "flex gap-4 animate-fade-in",
                msg.type === "user" ? "justify-end" : "justify-start"
                )}
            >
                {msg.type === 'ai' && (
                    <div className="h-8 w-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0 shadow-sm mt-1">
                        <span className="text-xs font-bold text-primary">AI</span>
                    </div>
                )}
                
                <div className={cn(
                    "rounded-2xl px-6 py-3.5 text-sm max-w-[85%] shadow-sm leading-relaxed",
                    msg.type === "user" 
                        ? "bg-primary text-primary-foreground rounded-tr-sm" 
                        : "bg-card border border-white/5 rounded-tl-sm text-foreground/90",
                    msg.content.includes("❌") && "bg-destructive/10 text-destructive border-destructive/20"
                )}>
                    {/* Render Attachment if exists */}
                    {(msg.attachment_name || (Number(msg.id) > Date.now() - 10000 && msg.attachment_name)) && msg.attachment_name && (
                        <div className="flex items-center gap-3 p-3 mb-3 bg-background/10 rounded-xl border border-white/10 overflow-hidden mix-blend-luminosity hover:mix-blend-normal transition-all">
                            <div className="h-10 w-10 rounded-lg bg-white/20 flex items-center justify-center shrink-0">
                                <FileText className="h-5 w-5 text-current opacity-80" />
                            </div>
                            <div className="flex-1 min-w-0 text-left">
                                <p className="text-sm font-medium truncate opacity-90">{msg.attachment_name}</p>
                                <p className="text-xs opacity-60">Document</p>
                            </div>
                            {msg.attachment_url && (
                                    <a 
                                    href={msg.attachment_url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="p-2 hover:bg-white/20 rounded-full transition-colors"
                                    title="Download"
                                    >
                                    <Paperclip className="h-4 w-4" />
                                    </a>
                            )}
                        </div>
                    )}

                    {msg.content}
                </div>

                {msg.type === 'user' && (
                     <div className="h-8 w-8 rounded-lg bg-primary/20 border border-primary/10 flex items-center justify-center shrink-0 shadow-sm mt-1">
                        <span className="text-xs font-bold text-primary font-mono">U</span>
                     </div>
                )}
            </div>
            ))}
            <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="p-6 md:p-8 bg-gradient-to-t from-background via-background to-transparent pt-12">
        <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="max-w-3xl mx-auto relative flex flex-col gap-2 bg-card/80 backdrop-blur-xl border border-white/10 rounded-2xl px-4 py-3 shadow-2xl ring-1 ring-white/5 focus-within:ring-primary/50 transition-all">
          
          {selectedFile && (
              <div className="flex items-center gap-2 p-2 bg-muted/20 rounded-lg border border-white/5 w-fit mb-1 animate-fade-in">
                  <div className="h-8 w-8 bg-primary/10 rounded flex items-center justify-center">
                      <FileText className="h-4 w-4 text-primary" />
                  </div>
                  <span className="text-sm text-muted-foreground truncate max-w-[150px]">{selectedFile.name}</span>
                  <button 
                    type="button"
                    onClick={() => setSelectedFile(null)}
                    className="ml-2 hover:bg-white/10 rounded-full p-1 transition-colors"
                  >
                      <X className="h-3 w-3 text-muted-foreground hover:text-foreground" />
                  </button>
              </div>
          )}

          <div className="flex items-center w-full">
            {isAdmin && (
                <div className="mr-3">
                <input
                    type="file"
                    id="file-upload"
                    className="hidden"
                    onChange={handleFileSelect}
                />
                <label 
                    htmlFor="file-upload" 
                    className="flex h-9 w-9 items-center justify-center rounded-xl bg-muted/50 hover:bg-primary/20 hover:text-primary cursor-pointer transition-all text-muted-foreground"
                    title="Upload Policy Document"
                >
                    <Paperclip className="h-4 w-4" />
                </label>
                </div>
            )}
            
            <input 
                value={input} 
                onChange={(e) => setInput(e.target.value)} 
                placeholder="Message AI Assistant..." 
                className="flex-1 bg-transparent border-none focus:outline-none text-base px-2 text-foreground placeholder:text-muted-foreground/50"
            />
            
            <Button 
                type="submit" 
                size="icon" 
                disabled={loading || (!input.trim() && !selectedFile)}
                className={cn(
                    "h-9 w-9 rounded-xl transition-all shadow-md ml-2",
                    (input.trim() || selectedFile)
                    ? "bg-primary text-primary-foreground hover:bg-primary/90 hover:scale-105" 
                    : "bg-muted text-muted-foreground"
                )}
            >
                {loading ? <div className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin" /> : <ArrowUp className="h-5 w-5" />}
            </Button>
          </div>
        </form>
        <p className="text-xs text-center text-muted-foreground mt-3 font-medium opacity-70">
            Multi-Agent HR Assistant v1.0 • AI can make mistakes.
        </p>
      </div>
    </div>
  )
}
