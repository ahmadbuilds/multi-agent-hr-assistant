export interface HITLTaskData {
  ticket_type?: string;
  subject?: string;
  description?: string;
  leave_days?: number | null;
  [key: string]: unknown; // Safer than any
}

export interface HITLEventPayload {
  hitl_task: HITLTaskData;
  conversation_id?: string;
  user_id?: string;
  [key: string]: unknown;
}

export interface SocketMessagePayload {
    channel: string;
    event_data: HITLEventPayload;
}
