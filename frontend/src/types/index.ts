export type SeverityLevel = "critical" | "high" | "medium" | "low";

export interface Alert {
  alert_id: string;
  timestamp: string;
  severity: SeverityLevel;
  category: string;
  title: string;
  description: string;
  evidence: string[];
  recommended_actions: string[];
  contributing_agents: string[];
  confidence: number;
  location: string;
  status: "active" | "confirmed" | "dismissed";
  camera_id?: string;
  frame_snapshot?: string;
}

export interface AlertFeedback {
  alert_id: string;
  outcome: "confirmed" | "dismissed";
  officer_note?: string;
}

export interface WsMessage {
  type: "alert" | "ack" | "feedback";
  data?: unknown;
}
