import Link from "next/link";
import { Suspense } from "react";
import { MessageCircle } from "lucide-react";

import { PatientSelector } from "@/components/dashboard/patient-selector";

const LINKS = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/ddx", label: "Differential Dx" },
  { href: "/dashboard/treatment", label: "Treatment" },
  { href: "/dashboard/risk", label: "Risk" },
  { href: "/dashboard/monitoring", label: "Monitoring" },
  { href: "/dashboard/audit", label: "Audit" },
  { href: "/chat", label: "Patient Chat" },
];

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>): JSX.Element {
  return (
    <main className="mx-auto min-h-screen max-w-7xl px-6 py-8">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Clinical Dashboard</h1>
          <p className="text-sm text-slate-600">Output, monitoring, and human-in-the-loop controls.</p>
        </div>
        <Suspense fallback={<div className="h-10 w-40 rounded-md border bg-slate-100" />}>
          <PatientSelector />
        </Suspense>
      </header>
      <nav className="mb-6 flex flex-wrap gap-2">
        {LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
          >
            {link.label === "Patient Chat" ? <MessageCircle className="h-4 w-4" /> : null}
            {link.label}
          </Link>
        ))}
      </nav>
      {children}
    </main>
  );
}

