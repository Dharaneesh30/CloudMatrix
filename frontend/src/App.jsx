import { useState } from "react";
import "./App.css";
import TaskForm from "./components/TaskForm";
import TaskList from "./components/TaskList";
import SortButton from "./components/SortButton";

function App() {
  const [tasks, setTasks] = useState([]);

  const addTask = (task) => {
    setTasks([...tasks, task]);
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>CloudMatrix</h1>
        <p>AI-Based Cloud Resource Allocation And Load Balancing System</p>
      </header>

      <main className="main-content">
        <TaskForm addTask={addTask} />
        <SortButton />
        <TaskList tasks={tasks} />
      </main>

      <footer className="footer">
        <p>© 2026 CloudMatrix | Team Project</p>
      </footer>
    <div style={{ padding: "20px" }}>
      <h1>CloudMatrix - Divide & Conquer</h1>

      <TaskForm addTask={addTask} />
      <SortButton />
      <TaskList tasks={tasks} />
    </div>
    </div>
  );
}

export default App;