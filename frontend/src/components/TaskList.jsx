export default function TaskList({ tasks = [] }) {

  if (tasks.length === 0) {
    return <p>No tasks available</p>
  }

  return (

    <div>

      <h3>Task List</h3>

      <ul>
        {tasks.map((task, index) => (
          <li key={index}>
            Task {task.id} | Priority {task.priority}
          </li>
        ))}
      </ul>

    </div>

  )
}