import Link from "next/link";

export default function Home(): JSX.Element {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-6 py-16">
      <p className="text-sm font-medium uppercase tracking-wide text-slate-500">
        Autonomous Multimodal Clinical AI Assistant
      </p>
      <h1 className="mt-2 text-4xl font-semibold tracking-tight text-slate-900">
        Welcome to AMCA
      </h1>
      <p className="mt-4 text-lg text-slate-600">Open the integrated clinical dashboard to review recommendations.</p>
      <Link
        href="/dashboard"
        className="mt-6 inline-flex w-fit items-center rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
      >
        Go to Dashboard
      </Link>
    </main>
  );
}
