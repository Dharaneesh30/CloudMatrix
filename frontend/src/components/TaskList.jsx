function TaskList({ tasks }) {
  return (
    <div className="task-box">
      <h3>Task List</h3>

      {tasks.length === 0 ? (
        <p className="empty-text">No tasks added yet</p>
      ) : (
        <ul className="task-list">
          {tasks.map((task, index) => (
            <li key={index} className="task-item">
              <span className="task-id">{task.task_id}</span>
              <span className="task-priority">
                Priority: {task.priority}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default TaskList;