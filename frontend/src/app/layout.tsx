import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "AI Incident Response Platform",
  description: "AI Engineering Incident Response & Autonomous Debugging Platform",
};
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
