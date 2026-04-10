export type ChatRole = "user" | "assistant" | "system";
export type UrgencyLevel = "normal" | "watch" | "urgent" | "emergency";

export interface ChatMessage {
  role: ChatRole;
  content: string;
  timestamp: string;
}

export interface ChatSession {
  session_id: string;
  patient_id: string;
  messages: ChatMessage[];
  created_at: string;
  last_active: string;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  urgency_level: UrgencyLevel;
  urgency_reason: string | null;
  suggested_actions: string[];
  disclaimer: string;
}

export interface PatientProfile {
  id: string;
  full_name: string;
  blood_group: string | null;
  allergies: string[];
}

export interface Prescription {
  id: string;
  medications: Array<{
    name?: string;
    dose?: string;
    frequency?: string;
    duration?: string;
  }>;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? process.env.INTERNAL_API_URL ?? "http://localhost:8000";

function sessionStorageKey(patientId: string): string {
  return `chat:session:${patientId}`;
}

export function getStoredSessionId(patientId: string): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(sessionStorageKey(patientId));
}

export function setStoredSessionId(patientId: string, sessionId: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(sessionStorageKey(patientId), sessionId);
}

export async function sendMessage(
  patient_id: string,
  session_id: string | null,
  message: string,
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ patient_id, session_id, message }),
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Chat request failed: ${response.status}`);
  return (await response.json()) as ChatResponse;
}

export async function getSession(sessionId: string): Promise<ChatSession> {
  const response = await fetch(`${API_BASE}/chat/session/${sessionId}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Session fetch failed: ${response.status}`);
  return (await response.json()) as ChatSession;
}

export async function getPatientProfile(patientId: string): Promise<PatientProfile> {
  const response = await fetch(`${API_BASE}/patients/${patientId}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Patient fetch failed: ${response.status}`);
  return (await response.json()) as PatientProfile;
}

export async function getPatientPrescriptions(patientId: string): Promise<Prescription[]> {
  const response = await fetch(`${API_BASE}/patients/${patientId}/prescriptions?limit=20&offset=0`, {
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Prescription fetch failed: ${response.status}`);
  return (await response.json()) as Prescription[];
}

