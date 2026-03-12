import { Sidebar } from "@/components/sidebar"
import { getChats } from "@/lib/actions"
export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const chats = await getChats()
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar chats={chats} />
      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        {children}
      </main>
    </div>
  )
}
