"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useSocket } from "@/components/socket-provider" 
import { toast } from "sonner"
import { createClient } from "@/lib/supabase/client"
import { HITLEventPayload, TicketCreationDetails, TicketCreationClassification, SocketMessagePayload, LibrarianTask } from "@/types/hitl"

interface HITLRequestModalProps {
  userId: string
  conversationId: string
}

export function HITLRequestModal({ userId, conversationId }: HITLRequestModalProps) {
  const { socket } = useSocket()
  const [isOpen, setIsOpen] = useState(false)
  const [taskData, setTaskData] = useState<TicketCreationDetails | null>(null)
  const [librarianTask, setLibrarianTask] = useState<LibrarianTask | null>(null)
  const [agentName, setAgentName] = useState<"Clerk" | "Librarian" | "">("")
  const [formData, setFormData] = useState<TicketCreationDetails>({} as TicketCreationDetails)
  const [loading, setLoading] = useState(false)
  const [showConfirmation, setShowConfirmation] = useState(false)

  const resetModalState = () => {
    setIsOpen(false)
    setShowConfirmation(false)
    setTaskData(null)
    setLibrarianTask(null)
    setAgentName("")
  }


  const handleHITLEventRef = useRef<((data: HITLEventPayload | undefined, channelName: string) => void) | null>(null)

  handleHITLEventRef.current = useCallback((data: HITLEventPayload | undefined, channelName: string) => {
    console.log("HITL Event Received:", data)
    if (!data) return

    if (channelName.endsWith("Clerk") && data.hitl_task) {
      if (data.hitl_task.action === "ticket_creation") {
        const details = (data.hitl_task as TicketCreationClassification).details
        setAgentName("Clerk")
        setTaskData(details)
        setFormData(details ?? {} as TicketCreationDetails)
        setShowConfirmation(false)
        setIsOpen(true)
      }
    } else if (channelName.endsWith("Librarian") && data.hitl_task) {
      let parsedTask: LibrarianTask
      if (typeof data.hitl_task === "string") {
        parsedTask = JSON.parse(data.hitl_task) as LibrarianTask
      } else {
        parsedTask = data.hitl_task as unknown as LibrarianTask
      }
      if (parsedTask && parsedTask.status === "waiting_for_human") {
        setAgentName("Librarian")
        setLibrarianTask(parsedTask)
        setIsOpen(true)
      }
    }
  }, [])

  useEffect(() => {
    if (!socket || !userId || !conversationId) return

    const clerkChannel = `HITL_Intervention_Channel:${userId}:${conversationId}:Clerk`
    const librarianChannel = `HITL_Intervention_Channel:${userId}:${conversationId}:Librarian`

    console.log("Subscribing to HITL channels")

    const clerkHandler = (data: HITLEventPayload | undefined) =>
      handleHITLEventRef.current?.(data, clerkChannel)
    const librarianHandler = (data: HITLEventPayload | undefined) =>
      handleHITLEventRef.current?.(data, librarianChannel)
    const messageHandler = (data: SocketMessagePayload) => {
      if (data?.channel === clerkChannel || data?.channel === librarianChannel) {
        handleHITLEventRef.current?.(data.event_data, data.channel)
      }
    }

    socket.on(clerkChannel, clerkHandler)
    socket.on(librarianChannel, librarianHandler)
    socket.on("message", messageHandler)

    return () => {
      socket.off(clerkChannel, clerkHandler)
      socket.off(librarianChannel, librarianHandler)
      socket.off("message", messageHandler)
    }
  }, [socket, userId, conversationId])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev: TicketCreationDetails) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (
    librarianConfirmValue?: boolean,
    clerkAcceptedOverride?: boolean
  ) => {
    setLoading(true)
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      
      let bodyData;
      if (agentName === "Librarian") {
          bodyData = {
              detail: librarianConfirmValue,
              conversation_id: conversationId,
              user_id: userId,
              agent_name: "Librarian"
          }
      } else {
          bodyData = {
              ...formData,
            accepted: clerkAcceptedOverride ?? (showConfirmation ? true : undefined),
              status: "in_progress",
              conversation_id: conversationId,
              user_id: userId,
              agent_name: "Clerk"
          }
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/hitl_response`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session?.access_token || ''}`
        },
        body: JSON.stringify(bodyData),
      })

      if (!response.ok) {
        throw new Error("Failed to submit HITL response")
      }

      toast.success("Response submitted successfully")
      resetModalState()
    } catch (error) {
      console.error("Error submitting HITL response:", error)
      toast.error("Failed to submit response. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleClerkReject = async () => {
    if (loading) return

    setLoading(true)
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/hitl_response`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session?.access_token || ''}`
        },
        body: JSON.stringify({
          accepted: false,
          conversation_id: conversationId,
          user_id: userId,
          agent_name: "Clerk"
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to submit HITL rejection")
      }

      toast.success("Request rejected")
      resetModalState()
    } catch (error) {
      console.error("Error submitting HITL rejection:", error)
      toast.error("Failed to reject request. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleCloseAndReject = async () => {
    if (loading) return

    if (agentName === "Librarian") {
      await handleSubmit(false)
      return
    }

    await handleClerkReject()
  }
  
  const handleInitialSubmit = (e: React.FormEvent) => {
      e.preventDefault()
    
      if (formData.ticket_type === 'leave' && !formData.leave_days) {
          toast.error("Please specify the number of leave days.")
          return
      }

      if (formData.ticket_type === 'leave' || formData.ticket_type === 'complaint') {
          setShowConfirmation(true)
      } else {
          handleSubmit()
      }
  }


  if (!isOpen || (!taskData && !librarianTask)) return null

  if (agentName === "Librarian" && librarianTask) {
      return (
        <Dialog
          open={isOpen}
          onOpenChange={(open) => {
            if (!open) {
              void handleCloseAndReject()
            }
          }}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Confirm Policy Document Update</DialogTitle>
            </DialogHeader>
            <div className="py-4 space-y-2 text-sm text-foreground/80">
                <p className="mb-4">Are you sure you want to proceed with this policy update?</p>
                <p><strong>Query:</strong> {librarianTask.query}</p>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <Button variant="destructive" onClick={() => handleSubmit(false)} disabled={loading}>
                  {loading ? "Submitting..." : "Reject"}
              </Button>
              <Button onClick={() => handleSubmit(true)} disabled={loading}>
                  {loading ? "Submitting..." : "Accept"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )
  }

  if (showConfirmation && taskData) {
      return (
        <Dialog
          open={isOpen}
          onOpenChange={(open) => {
            if (!open) {
              void handleCloseAndReject()
            }
          }}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Confirm {formData.ticket_type === 'leave' ? 'Leave Request' : 'Complaint'}</DialogTitle>
          </DialogHeader>
          <div className="py-4 space-y-2 text-sm text-foreground/80">
              <p className="mb-4">Are you sure you want to create this {formData.ticket_type} ticket?</p>
              <p><strong>Subject:</strong> {formData.subject}</p>
              <p><strong>Description:</strong> {formData.description}</p>
               {formData.ticket_type === 'leave' && <p><strong>Leave Days:</strong> {formData.leave_days}</p>}
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setShowConfirmation(false)} disabled={loading}>Back</Button>
            <Button variant="destructive" onClick={() => void handleClerkReject()} disabled={loading}>
                {loading ? "Submitting..." : "Cancel"}
            </Button>
            <Button onClick={() => handleSubmit()} disabled={loading}>
                {loading ? "Submitting..." : "Yes, I'm sure"}
            </Button>
          </div>
          </DialogContent>
        </Dialog>
      )
  }

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) {
          void handleCloseAndReject()
        }
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Additional Information Required</DialogTitle>
          <p className="text-sm text-muted-foreground mt-1.5">
            The agent needs some more details to proceed with your request.
          </p>
        </DialogHeader>
        <form onSubmit={handleInitialSubmit} className="space-y-4 py-4">
          <div className="space-y-2">
             <Label htmlFor="ticket_type">Ticket Type</Label>
             <Input 
                id="ticket_type" 
                name="ticket_type" 
                value={formData.ticket_type || ''} 
                onChange={handleChange}
                placeholder="e.g., leave, complaint, general"
             />
          </div>

          <div className="space-y-2">
             <Label htmlFor="subject">Subject</Label>
             <Input 
                id="subject" 
                name="subject" 
                value={formData.subject || ''} 
                onChange={handleChange} 
                placeholder="Subject of your ticket"
             />
          </div>

          <div className="space-y-2">
             <Label htmlFor="description">Description</Label>
             <Textarea 
                id="description" 
                name="description" 
                value={formData.description || ''} 
                onChange={handleChange} 
                placeholder="Detailed description..."
             />
          </div>

          {(formData.ticket_type === 'leave' || taskData?.ticket_type === 'leave') && (
              <div className="space-y-2">
                  <Label htmlFor="leave_days">Number of Leave Days</Label>
                   <Input 
                    type="number"
                    id="leave_days" 
                    name="leave_days" 
                    value={formData.leave_days || ''} 
                    onChange={handleChange} 
                    placeholder="e.g. 1, 2, 5"
                 />
              </div>
          )}
          
          <div className="flex justify-end gap-2 mt-4">
            <Button type="button" variant="destructive" onClick={() => void handleClerkReject()} disabled={loading}>
                {loading ? "Submitting..." : "Cancel "}
            </Button>
            <Button type="submit" disabled={loading}>
                {loading ? "Submitting..." : "Submit Response"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}