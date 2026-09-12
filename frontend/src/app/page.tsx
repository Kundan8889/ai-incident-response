export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      <div className="z-10 max-w-3xl w-full text-center space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-medium tracking-wide">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Phase 0: Foundation Active
        </div>
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
          AI Incident Response Platform
        </h1>
        <p className="text-base sm:text-lg text-slate-400 max-w-xl mx-auto">
          Autonomous engineering incident triage, root cause analysis, and guided remediation workflow foundation.
        </p>
        <div className="pt-4 flex items-center justify-center gap-4 text-xs text-slate-500">
          <span className="px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700/60">FastAPI Backend</span>
          <span className="text-slate-600">?</span>
          <span className="px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700/60">Next.js App Router</span>
          <span className="text-slate-600">?</span>
          <span className="px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700/60">Tailwind CSS</span>
        </div>
      </div>
    </main>
  );
}
