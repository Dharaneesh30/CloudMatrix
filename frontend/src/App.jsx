import { useState } from "react";
import TaskForm from "./components/TaskForm";
import TaskList from "./components/TaskList";
import SortButton from "./components/SortButton";

function App() {
  const [tasks, setTasks] = useState([]);

  const addTask = (task) => {
    setTasks([...tasks, task]);
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>CloudMatrix - Divide & Conquer</h1>

      <TaskForm addTask={addTask} />
      <SortButton />
      <TaskList tasks={tasks} />
    </div>
  );
}

export default App;