export interface TicketCreationDetails {
  ticket_type: string;
  subject: string;
  description: string;
  leave_days?: number | null;
  accepted?: boolean | null;
  status?: string;
  [key: string]: unknown;
}

export interface TicketCreationClassification {
  action: "ticket_creation";
  details: TicketCreationDetails;
}

export interface OtherClassification {
  action: string;
  details?: unknown;
}

export type ClerkClassificationState = TicketCreationClassification | OtherClassification;

export interface LibrarianTask {
  action: string;
  query: string;
  status: string;
  result?: string | null;
  hitl_response?: boolean | null;
  [key: string]: unknown;
}

export interface HITLEventPayload {
  hitl_task?: ClerkClassificationState;
  action?: string | LibrarianTask; 
  agent?: string; 
  conversation_id?: string;
  user_id?: string;
  [key: string]: unknown;
}

export interface SocketMessagePayload {
  channel: string;
  event_data: HITLEventPayload;
  agent_name?: string;
}
