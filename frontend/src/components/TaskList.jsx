function TaskList({ tasks }) {
  return (
    <div>
      <h3>Task List</h3>

      <ul>
        {tasks.map((task, index) => (
          <li key={index}>
            {task.task_id} - Priority: {task.priority}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default TaskList;