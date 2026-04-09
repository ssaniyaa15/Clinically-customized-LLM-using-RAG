"use client";

import {
  Line,
  LineChart,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type SurvivalPoint = { t: number; s: number };

export function RiskChart({
  probability,
  survival,
}: {
  probability: number;
  survival: SurvivalPoint[];
}): JSX.Element {
  const gaugeData = [{ name: "Readmission", value: Math.round(probability * 100), fill: "#0f172a" }];
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="h-64 rounded-lg border bg-white p-3">
        <p className="mb-2 text-sm font-medium text-slate-700">Readmission Probability</p>
        <ResponsiveContainer width="100%" height="90%">
          <RadialBarChart data={gaugeData} startAngle={180} endAngle={0} innerRadius="60%" outerRadius="100%">
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar background dataKey="value" />
            <Tooltip />
          </RadialBarChart>
        </ResponsiveContainer>
      </div>
      <div className="h-64 rounded-lg border bg-white p-3">
        <p className="mb-2 text-sm font-medium text-slate-700">Survival Curve</p>
        <ResponsiveContainer width="100%" height="90%">
          <LineChart data={survival}>
            <XAxis dataKey="t" />
            <YAxis domain={[0, 1]} />
            <Tooltip />
            <Line type="monotone" dataKey="s" stroke="#0f172a" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

