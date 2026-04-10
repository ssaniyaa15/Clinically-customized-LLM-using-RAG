"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? process.env.INTERNAL_API_URL ?? "http://localhost:8000";

interface RecordUploaderProps {
  patientId: string;
}

const ACCEPT = ".pdf,.jpg,.jpeg,.png,.dcm,application/pdf,image/jpeg,image/png";

export function RecordUploader({ patientId }: RecordUploaderProps): JSX.Element {
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [recordType, setRecordType] = useState("lab_report");
  const [notes, setNotes] = useState("");
  const [progress, setProgress] = useState(0);
  const [toast, setToast] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const toastClass = useMemo(
    () =>
      `fixed right-4 top-4 z-50 rounded-md px-3 py-2 text-sm shadow ${
        toast?.toLowerCase().includes("error")
          ? "bg-red-600 text-white"
          : "bg-emerald-600 text-white"
      }`,
    [toast],
  );

  const upload = async (): Promise<void> => {
    if (!file) return;
    setUploading(true);
    setProgress(5);
    const form = new FormData();
    form.append("file", file);
    const xhr = new XMLHttpRequest();
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        setProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    xhr.onload = () => {
      setUploading(false);
      if (xhr.status >= 200 && xhr.status < 300) {
        setToast("Upload successful");
        setFile(null);
        setNotes("");
        setProgress(0);
      } else {
        setToast("Error: upload failed");
      }
      setTimeout(() => setToast(null), 2500);
    };
    xhr.onerror = () => {
      setUploading(false);
      setToast("Error: upload failed");
      setTimeout(() => setToast(null), 2500);
    };
    xhr.open(
      "POST",
      `${API_BASE}/patients/${patientId}/records?record_type=${encodeURIComponent(recordType)}&notes=${encodeURIComponent(notes)}`,
    );
    xhr.send(form);
  };

  return (
    <>
      {toast ? <div className={toastClass}>{toast}</div> : null}
      <Button type="button" variant="outline" onClick={() => setOpen((v) => !v)} className="w-full">
        {open ? "Close uploader" : "Upload records"}
      </Button>
      {open ? (
        <Card className="mt-3">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Record Upload</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <label className="flex cursor-pointer flex-col items-center rounded-md border border-dashed border-slate-300 p-4 text-xs text-slate-600 hover:bg-slate-50">
              <span>Drag and drop or click to choose a file</span>
              <input
                type="file"
                accept={ACCEPT}
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
            <select
              value={recordType}
              onChange={(e) => setRecordType(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-2 py-2 text-xs"
            >
              <option value="xray">X-ray</option>
              <option value="mri">MRI</option>
              <option value="ct">CT</option>
              <option value="lab_report">Lab report</option>
              <option value="prescription">Prescription</option>
              <option value="discharge_summary">Discharge summary</option>
              <option value="pathology">Pathology</option>
              <option value="other">Other</option>
            </select>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional notes"
              className="min-h-20 w-full rounded-md border border-slate-300 px-2 py-2 text-xs"
            />
            {uploading ? <Progress value={progress} /> : null}
            <Button type="button" onClick={() => void upload()} disabled={!file || uploading} className="w-full">
              {uploading ? "Uploading..." : "Upload"}
            </Button>
          </CardContent>
        </Card>
      ) : null}
    </>
  );
}

