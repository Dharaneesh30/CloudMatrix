import { Suspense, lazy } from "react";
import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";

import { PipelineProvider } from "./context/PipelineProvider";
import { usePipeline } from "./context/usePipeline";

const UploadPage = lazy(() => import("./pages/UploadPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const SchedulingPage = lazy(() => import("./pages/SchedulingPage"));
const ResultsPage = lazy(() => import("./pages/ResultsPage"));
const LoadBalancePage = lazy(() => import("./pages/LoadBalancePage"));

function AppShell() {
  const { hasRun, isCompleted, isProcessing, status } = usePipeline();
  const flowLocked = isProcessing;

  const steps = [
    { label: "1. Upload", route: "/", enabled: !flowLocked },
    { label: "2. Monitor", route: "/dashboard", enabled: hasRun || isProcessing || isCompleted },
    { label: "3. Scheduling", route: "/scheduling", enabled: !flowLocked && isCompleted },
    { label: "4. Allocation", route: "/load-balance", enabled: !flowLocked && (isCompleted || hasRun) },
    { label: "5. Results", route: "/results", enabled: !flowLocked && (isCompleted || hasRun) },
  ];

  return (
    <BrowserRouter>
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-5 px-4 py-6 md:px-6">
        <header className="glass-card hero-shell page-enter p-5 md:p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink/55">AI Cloud Scheduling System</p>
              <h1 className="font-display text-3xl font-bold tracking-tight md:text-4xl">CloudMatrix AI</h1>
              <p className="mt-1 text-sm text-ink/60">Pipeline-first scheduling with analytics and balancing</p>
            </div>

            <div className="rounded-xl border border-white/60 bg-white/82 px-3 py-2 text-sm">
              <span className="font-semibold capitalize">{status?.status || "idle"}</span>
              <span className="mx-2 text-ink/40">|</span>
              <span>{Number(status?.progress || 0)}%</span>
            </div>
          </div>

          <nav className="mt-5 flex flex-wrap gap-2">
            {steps.map((step) => {
              if (!step.enabled) {
                return (
                  <span
                    key={step.route}
                    className="cursor-not-allowed rounded-full border border-ink/10 bg-ink/5 px-4 py-2 text-sm font-semibold text-ink/35"
                  >
                    {step.label}
                  </span>
                );
              }

              return (
                <NavLink
                  key={step.route}
                  to={step.route}
                  end={step.route === "/"}
                  className={({ isActive }) =>
                    `rounded-full border px-4 py-2 text-sm font-semibold transition ${
                      isActive
                        ? "border-transparent bg-gradient-to-r from-ember to-orange-500 text-white shadow-[0_8px_18px_rgba(239,91,54,0.35)]"
                        : "border-ink/15 bg-white/80 text-ink hover:-translate-y-0.5 hover:bg-white"
                    }`
                  }
                >
                  {step.label}
                </NavLink>
              );
            })}
          </nav>
        </header>

        <main className="page-enter pb-6">
          <Suspense fallback={<div className="glass-card p-4 text-sm text-ink/70">Loading page...</div>}>
            <Routes>
              <Route path="/" element={<UploadPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/scheduling" element={<SchedulingPage />} />
              <Route path="/results" element={<ResultsPage />} />
              <Route path="/load-balance" element={<LoadBalancePage />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </BrowserRouter>
  );
}

function App() {
  return (
    <PipelineProvider>
      <AppShell />
    </PipelineProvider>
  );
}

export default App;
