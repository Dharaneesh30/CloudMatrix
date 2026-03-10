import { useState } from "react";

function TaskForm({ addTask }) {
  const [taskId, setTaskId] = useState("");
  const [priority, setPriority] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();

    const newTask = {
      task_id: taskId,
      priority: parseInt(priority),
    };

    addTask(newTask);

    setTaskId("");
    setPriority("");
  };

  return (
    <div>
      <h3>Add Task</h3>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Task ID"
          value={taskId}
          onChange={(e) => setTaskId(e.target.value)}
        />

        <input
          type="number"
          placeholder="Priority"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
        />

        <button type="submit">Add Task</button>
      </form>
    </div>
  );
}

export default TaskForm;