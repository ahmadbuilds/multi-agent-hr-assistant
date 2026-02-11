"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useSocket } from "@/components/socket-provider" // Adjust path as needed
import { toast } from "sonner"
import { createClient } from "@/lib/supabase/client"
import { HITLEventPayload, HITLTaskData, SocketMessagePayload } from "@/types/hitl"

interface HITLRequestModalProps {
  userId: string
  conversationId: string
}

export function HITLRequestModal({ userId, conversationId }: HITLRequestModalProps) {
  const { socket } = useSocket()
  const [isOpen, setIsOpen] = useState(false)
  const [taskData, setTaskData] = useState<HITLTaskData | null>(null)
  const [formData, setFormData] = useState<HITLTaskData>({})
  const [loading, setLoading] = useState(false)
  const [showConfirmation, setShowConfirmation] = useState(false)

  useEffect(() => {
    if (!socket || !userId || !conversationId) return

    const channel = `HITL_Intervention_Channel:${userId}:${conversationId}:Clerk`
    console.log(`Subscribing to ${channel}`)

    const handleHITLEvent = (data: HITLEventPayload | undefined) => {
        console.log("HITL Event Received:", data)
      if (data && data.hitl_task) {
        setTaskData(data.hitl_task)
        setFormData(data.hitl_task) // Initialize form with received data
        setIsOpen(true)
        setShowConfirmation(false) // Reset confirmation state
      }
    }

    // Subscribe to the channel/event
    socket.on(channel, handleHITLEvent)
    
    // Also listen for "message" event as a fallback
    socket.on("message", (data: SocketMessagePayload) => {
        if (data?.channel === channel) {
             handleHITLEvent(data.event_data)
        }
    })

    return () => {
      socket.off(channel, handleHITLEvent)
      socket.off("message")
    }
  }, [socket, userId, conversationId])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async () => {
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
          ...formData,
          conversation_id: conversationId,
          user_id: userId
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to submit HITL response")
      }

      toast.success("Response submitted successfully")
      setIsOpen(false)
    } catch (error) {
      console.error("Error submitting HITL response:", error)
      toast.error("Failed to submit response. Please try again.")
    } finally {
      setLoading(false)
    }
  }
  
  const handleInitialSubmit = (e: React.FormEvent) => {
      e.preventDefault()
      
      // Validation: Check if leave days is present for leave tickets
      if (formData.ticket_type === 'leave' && !formData.leave_days) {
          toast.error("Please specify the number of leave days.")
          return
      }

      // Confirmation: Ask for confirmation for leave or complaint tickets
      if (formData.ticket_type === 'leave' || formData.ticket_type === 'complaint') {
          setShowConfirmation(true)
      } else {
          handleSubmit()
      }
  }


  if (!isOpen || !taskData) return null

  if (showConfirmation) {
      return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
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
            <Button variant="outline" onClick={() => setShowConfirmation(false)}>Back</Button>
            <Button onClick={handleSubmit} disabled={loading}>
                {loading ? "Submitting..." : "Yes, I'm sure"}
            </Button>
          </div>
        </Dialog>
      )
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
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

          {(formData.ticket_type === 'leave' || taskData.ticket_type === 'leave') && (
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
            <Button type="submit" disabled={loading}>
                {loading ? "Submitting..." : "Submit Response"}
            </Button>
          </div>
        </form>
    </Dialog>
  )
}
