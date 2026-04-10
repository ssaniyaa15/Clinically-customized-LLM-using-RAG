"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const STORAGE_KEY = "chat:selected-patient-id";

export default function ChatLandingPage(): JSX.Element {
  const [patientId, setPatientId] = useState("");
  const router = useRouter();

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved) setPatientId(saved);
  }, []);

  const submit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (!patientId.trim()) return;
    window.localStorage.setItem(STORAGE_KEY, patientId.trim());
    router.push(`/chat/${patientId.trim()}`);
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-lg items-center px-4 py-10">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Patient Chat</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-3">
            <label className="text-sm font-medium text-slate-700">Patient ID</label>
            <input
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              placeholder="Enter patient UUID"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
            <Button type="submit" className="w-full">
              Continue to chat
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}

