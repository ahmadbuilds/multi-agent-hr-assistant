import { ChatArea } from "@/components/chat-area"
import { getMessages } from "@/lib/actions"

export default async function ChatPage({ params }: { params: Promise<{ chatId: string }> }) {
  const { chatId } = await params
  const messages = await getMessages(chatId)
  return <ChatArea chatId={chatId} initialMessages={messages} />
}
