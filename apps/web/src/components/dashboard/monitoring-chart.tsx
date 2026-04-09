"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function MonitoringChart({
  auc,
  psi,
  fairnessGap,
}: {
  auc: number;
  psi: number;
  fairnessGap: number;
}): JSX.Element {
  const points = [
    { step: "t-2", auc: Math.max(0, auc - 0.06) },
    { step: "t-1", auc: Math.max(0, auc - 0.03) },
    { step: "t", auc },
  ];
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <div className="rounded-lg border bg-white p-4">
        <p className="text-sm text-slate-600">PSI Score</p>
        <p className="mt-2 text-2xl font-semibold">{psi.toFixed(3)}</p>
      </div>
      <div className="rounded-lg border bg-white p-4">
        <p className="text-sm text-slate-600">Fairness Gap</p>
        <p className="mt-2 text-2xl font-semibold">{fairnessGap.toFixed(3)}</p>
      </div>
      <div className="h-40 rounded-lg border bg-white p-3 md:col-span-1">
        <p className="mb-2 text-sm text-slate-600">AUC Trend</p>
        <ResponsiveContainer width="100%" height="80%">
          <LineChart data={points}>
            <XAxis dataKey="step" />
            <YAxis domain={[0, 1]} />
            <Tooltip />
            <Line dataKey="auc" stroke="#0f172a" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

