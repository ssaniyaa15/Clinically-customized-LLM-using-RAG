"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PrescriptionCard } from "@/components/chat/PrescriptionCard";
import { RecordUploader } from "@/components/chat/RecordUploader";
import { getPatientProfile, type PatientProfile } from "@/lib/chat-api";
import { useChat } from "@/hooks/useChat";

const QUICK_PROMPTS = [
  "What are my current medications?",
  "Explain my last lab report",
  "I have a headache, what should I do?",
  "When is my next follow-up?",
];

function urgencyStyle(level: string): string {
  if (level === "emergency") return "border-l-4 border-red-600 bg-red-50";
  if (level === "urgent") return "border-l-4 border-orange-500 bg-orange-50";
  if (level === "watch") return "border-l-4 border-yellow-500";
  return "border-l-4 border-green-500";
}

function urgencyBadge(level: string): string {
  if (level === "emergency") return "🔴 Emergency";
  if (level === "urgent") return "🟠 Urgent";
  if (level === "watch") return "🟡 Watch";
  return "🟢 Normal";
}

export default function PatientChatPage({
  params,
}: {
  params: { patient_id: string };
}): JSX.Element {
  const patientId = params.patient_id;
  const [patient, setPatient] = useState<PatientProfile | null>(null);
  const [text, setText] = useState("");
  const [showEmergencyBanner, setShowEmergencyBanner] = useState(true);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const { messages, isLoading, sendMessage, urgencyLevel, error, dismissEmergencyBanner } = useChat(patientId);

  useEffect(() => {
    void getPatientProfile(patientId)
      .then(setPatient)
      .catch(() => setPatient(null));
  }, [patientId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    if (urgencyLevel === "emergency") setShowEmergencyBanner(true);
    else setShowEmergencyBanner(false);
  }, [urgencyLevel]);

  const sendCurrent = async (): Promise<void> => {
    const payload = text.trim();
    if (!payload) return;
    setText("");
    setShowEmergencyBanner(false);
    await sendMessage(payload);
  };

  const sidebarAllergies = useMemo(
    () => (patient?.allergies && patient.allergies.length > 0 ? patient.allergies.join(", ") : "None known"),
    [patient],
  );

  return (
    <main className="mx-auto flex min-h-screen max-w-7xl gap-4 px-4 py-6">
      <aside className="w-[240px] shrink-0">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Patient Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-slate-700">
            <p className="font-medium">{patient?.full_name ?? "Loading..."}</p>
            <p>Blood group: {patient?.blood_group ?? "Unknown"}</p>
            <p>Allergies: {sidebarAllergies}</p>
          </CardContent>
        </Card>
        <RecordUploader patientId={patientId} />
        <PrescriptionCard patientId={patientId} />
      </aside>

      <section className="flex min-h-[80vh] flex-1 flex-col rounded-lg border border-slate-200 bg-white">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h2 className="text-lg font-semibold">AI Nurse Assistant</h2>
          <div className="flex items-center gap-2 text-xs text-emerald-700">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
            Online
          </div>
        </div>

        {urgencyLevel === "emergency" && showEmergencyBanner ? (
          <div className="flex items-center justify-between bg-red-600 px-4 py-2 text-sm text-white">
            <span>⚠️ This sounds like a medical emergency. Call 112 or 911 immediately.</span>
            <button
              type="button"
              onClick={() => {
                setShowEmergencyBanner(false);
                dismissEmergencyBanner();
              }}
              className="rounded border border-white/50 px-2 py-0.5 text-xs"
            >
              Dismiss
            </button>
          </div>
        ) : null}

        <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
          {messages.map((msg, index) => {
            const isUser = msg.role === "user";
            return (
              <div key={`${msg.timestamp}-${index}`} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                {isUser ? (
                  <div className="max-w-[75%] rounded-2xl bg-violet-600 px-4 py-2 text-sm text-white">
                    {msg.content}
                  </div>
                ) : (
                  <div
                    className={`max-w-[80%] rounded-lg border px-3 py-3 text-sm ${urgencyStyle(
                      msg.urgencyLevel ?? "normal",
                    )}`}
                  >
                    <p className="whitespace-pre-wrap text-slate-800">{msg.content}</p>
                    <div className="mt-2">
                      <Badge>{urgencyBadge(msg.urgencyLevel ?? "normal")}</Badge>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {(msg.suggestedActions ?? ["Follow your prescription", "Schedule a routine checkup"]).map(
                        (action) => (
                        <button
                          key={action}
                          type="button"
                          className="rounded-full border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-700"
                        >
                          {action}
                        </button>
                        ),
                      )}
                    </div>
                    <p className="mt-2 text-[11px] text-slate-500">
                      {msg.disclaimer ??
                        "This is an AI assistant. Always consult your doctor for medical decisions."}
                    </p>
                  </div>
                )}
              </div>
            );
          })}

          {isLoading ? (
            <div className="flex justify-start">
              <div className="rounded-lg border bg-white px-3 py-2">
                <div className="flex items-center gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
                </div>
              </div>
            </div>
          ) : null}
          <div ref={bottomRef} />
        </div>

        <div className="border-t px-4 py-3">
          <div className="mb-2 flex flex-wrap gap-2">
            {QUICK_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                className="rounded-full border border-slate-300 bg-slate-50 px-3 py-1 text-xs text-slate-700 hover:bg-slate-100"
                onClick={() => setText(prompt)}
              >
                {prompt}
              </button>
            ))}
          </div>
          {error ? <p className="mb-2 text-xs text-red-600">{error}</p> : null}
          <div className="flex gap-2">
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void sendCurrent();
              }}
              placeholder="Type your message..."
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
            <Button type="button" onClick={() => void sendCurrent()} disabled={isLoading || !text.trim()}>
              Send
            </Button>
          </div>
        </div>
      </section>
    </main>
  );
}

