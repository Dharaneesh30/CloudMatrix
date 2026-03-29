import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";

import UploadPage from "./pages/UploadPage";
import DashboardPage from "./pages/DashboardPage";
import SchedulingPage from "./pages/SchedulingPage";
import ResultsPage from "./pages/ResultsPage";
import LoadBalancePage from "./pages/LoadBalancePage";
import { PipelineProvider, usePipeline } from "./context/PipelineContext";

function AppShell() {
  const { hasRun, isCompleted, isProcessing, status } = usePipeline();

  const steps = [
    { label: "1. Upload", route: "/", enabled: true },
    { label: "2. Monitor", route: "/dashboard", enabled: hasRun || isProcessing || isCompleted },
    { label: "3. Scheduling", route: "/scheduling", enabled: isCompleted },
    { label: "4. Results", route: "/results", enabled: isCompleted || hasRun },
    { label: "5. Balance", route: "/load-balance", enabled: isCompleted || hasRun },
  ];

  return (
    <BrowserRouter>
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-5 px-4 py-6 md:px-6">
        <header className="glass-card page-enter p-5">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink/55">AI Cloud Scheduling System</p>
              <h1 className="font-display text-3xl font-bold tracking-tight">CloudMatrix AI</h1>
            </div>

            <div className="rounded-xl bg-white/70 px-3 py-2 text-sm">
              <span className="font-semibold capitalize">{status?.status || "idle"}</span>
              <span className="mx-2 text-ink/40">|</span>
              <span>{Number(status?.progress || 0)}%</span>
            </div>
          </div>

          <nav className="mt-4 flex flex-wrap gap-2">
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
                        ? "border-transparent bg-ember text-white"
                        : "border-ink/15 bg-white/80 text-ink hover:-translate-y-0.5"
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
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/scheduling" element={<SchedulingPage />} />
            <Route path="/results" element={<ResultsPage />} />
            <Route path="/load-balance" element={<LoadBalancePage />} />
          </Routes>
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
