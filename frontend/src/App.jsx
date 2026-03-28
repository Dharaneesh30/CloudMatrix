import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import TaskSorting from "./pages/TaskSorting";
import ServerAllocation from "./pages/ServerAllocation";

import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <div className="bg-orb bg-orb-1" />
        <div className="bg-orb bg-orb-2" />

        <header className="header">
          <div className="brand">
            <p className="brand-kicker">Distributed Scheduling Console</p>
            <h1>CloudMatrix</h1>
          </div>

          <nav className="nav">
            <NavLink to="/" end>
              Upload Dataset
            </NavLink>
            <NavLink to="/task-sorting">Task Sorting</NavLink>
            <NavLink to="/server-allocation">Server Allocation</NavLink>
          </nav>
        </header>

        <main className="content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/task-sorting" element={<TaskSorting />} />
            <Route path="/server-allocation" element={<ServerAllocation />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
