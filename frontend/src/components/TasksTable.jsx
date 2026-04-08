export default function TasksTable({ tasks = [] }) {
  if (!tasks.length) {
    return <p className="text-sm text-ink/65">No tasks found.</p>;
  }

  return (
    <div className="table-shell">
      <table className="min-w-[1050px] w-full text-sm">
        <thead className="table-head text-left font-display text-xs uppercase tracking-wide text-ink/65">
          <tr>
            <th className="px-3 py-2">ID</th>
            <th className="px-3 py-2">Rank</th>
            <th className="px-3 py-2">Priority</th>
            <th className="px-3 py-2">CPU</th>
            <th className="px-3 py-2">Memory</th>
            <th className="px-3 py-2">Execution</th>
            <th className="px-3 py-2">Predicted</th>
            <th className="px-3 py-2">Priority Score</th>
            <th className="px-3 py-2">Server</th>
            <th className="px-3 py-2">Allocated</th>
            <th className="px-3 py-2">Task Status</th>
            <th className="px-3 py-2">Algo</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr key={task.id} className="table-row border-t border-ink/10">
              <td className="px-3 py-2 font-medium">{task.id}</td>
              <td className="px-3 py-2">{task.schedule_rank ?? "-"}</td>
              <td className="px-3 py-2">{Number(task.priority).toFixed(2)}</td>
              <td className="px-3 py-2">{Number(task.cpu_request).toFixed(2)}</td>
              <td className="px-3 py-2">{Number(task.memory_request).toFixed(2)}</td>
              <td className="px-3 py-2">{Number(task.execution_time).toFixed(2)}</td>
              <td className="px-3 py-2">{Number(task.predicted_execution_time).toFixed(2)}</td>
              <td className="px-3 py-2">{Number(task.priority_score).toFixed(2)}</td>
              <td className="px-3 py-2">{task.allocated_server || "unassigned"}</td>
              <td className="px-3 py-2">
                <span
                  className={`rounded-full px-2 py-1 text-xs font-semibold ${
                    Number(task.allocation_success) ? "bg-mint/20 text-mint" : "bg-red-100 text-red-600"
                  }`}
                >
                  {Number(task.allocation_success) ? "yes" : "no"}
                </span>
              </td>
              <td className="px-3 py-2">
                <span
                  className={`rounded-full px-2 py-1 text-xs font-semibold ${
                    task.task_status === "completed"
                      ? "bg-mint/20 text-mint"
                      : task.task_status === "queued"
                      ? "bg-sky-100 text-sky-700"
                      : "bg-red-100 text-red-600"
                  }`}
                >
                  {task.task_status || "unknown"}
                </span>
              </td>
              <td className="px-3 py-2">{task.scheduling_type || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
