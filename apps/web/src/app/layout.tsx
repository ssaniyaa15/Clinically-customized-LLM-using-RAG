import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "AMCA — Clinical AI Assistant",
  description: "Autonomous Multimodal Clinical AI Assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
