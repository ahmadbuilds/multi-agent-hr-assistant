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
  details?: any;
}

export type ClerkClassificationState = TicketCreationClassification | OtherClassification;

export interface HITLEventPayload {
  hitl_task: ClerkClassificationState;
  conversation_id?: string;
  user_id?: string; // Corrected from hitl.ts where it was user_id
  [key: string]: unknown;
}

export interface SocketMessagePayload {
  channel: string;
  event_data: HITLEventPayload;
}
