"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { MessageSquare, Plus, LogOut, Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import { getChats } from "@/lib/actions"
import { useEffect, useState, useRef } from "react"

export function Sidebar({ chats: initialChats }: { chats: any[] }) {
  const pathname = usePathname()
  const router = useRouter()
  const supabase = createClient()
  
  const [chats, setChats] = useState(initialChats)
  const [offset, setOffset] = useState(initialChats.length)
  const [loading, setLoading] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Sync state with server-updated props (e.g. after router.refresh())
  useEffect(() => {
    setChats(initialChats)
    setOffset(initialChats.length) 
    // Resetting offset/hasMore might be needed if the refresh resets the view, 
    // but usually just updating the list is what's expected.
    // Ideally we merge, but for now strict sync ensures the new chat shows up.
  }, [initialChats])

  const handleLogout = async () => {
    await supabase.auth.signOut()
    router.push('/auth/login')
    router.refresh()
  }

  const loadMore = async () => {
    if (loading || !hasMore) return
    setLoading(true)
    const newChats = await getChats(offset, 20)
    
    if (newChats.length < 20) {
      setHasMore(false)
    }
    
    setChats(prev => [...prev, ...newChats])
    setOffset(prev => prev + newChats.length)
    setLoading(false)
  }

  const onScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget
    if (scrollHeight - scrollTop <= clientHeight + 50) {
        loadMore()
    }
  }

  return (
    <div className="w-64 border-r bg-card/50 backdrop-blur-xl text-card-foreground flex flex-col h-full shadow-2xl z-50 transition-all duration-300">
      <div className="p-4 border-b">
        <Button 
          variant="secondary" 
          className="w-full justify-start gap-2 shadow-sm hover:brightness-110 transition-all font-medium py-4 h-10" 
          onClick={() => router.push('/dashboard')}
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>
      
      <div 
        className="flex-1 overflow-auto p-2 space-y-1 custom-scrollbar"
        onScroll={onScroll}
        ref={scrollRef}
      >
        <div className="px-2 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
          History
        </div>
        {chats.length === 0 && (
          <div className="text-sm text-muted-foreground px-3 py-2 italic text-center mt-4">No chats yet</div>
        )}
        {chats.map((chat) => (
          <Link
            key={chat.chat_id}
            href={`/dashboard/chat/${chat.chat_id}`}
            className={cn(
              "flex items-center gap-3 px-3 py-3 rounded-lg text-sm transition-all relative group",
              pathname === `/dashboard/chat/${chat.chat_id}` 
                ? "bg-primary/10 text-primary font-medium border border-primary/20" 
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <MessageSquare className="h-4 w-4 shrink-0 transition-transform group-hover:scale-110" />
            <span className="truncate flex-1">{chat.title}</span>
          </Link>
        ))}
        {loading && (
            <div className="flex justify-center p-2">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
            </div>
        )}
      </div>

      <div className="p-4 border-t bg-muted/20">
        <Button 
           variant="ghost" 
           className="w-full justify-start gap-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
           onClick={handleLogout}
        >
            <LogOut className="h-4 w-4" />
            Logout
        </Button>
      </div>
    </div>
  )
}
