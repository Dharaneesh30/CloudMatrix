import { useEffect, useState } from "react"
import api from "../services/api"

function TaskSorting() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [page, setPage] = useState(1)
  const [pageSize] = useState(100)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    const fetchTasks = async () => {
      setLoading(true)
      setError("")

      try {
        const res = await api.get("/sort-tasks", {
          params: { page, page_size: pageSize }
        })
        setTasks(res.data.tasks || [])
        setTotal(res.data.total || 0)
      } catch (err) {
        setError(
          err.response?.data?.error ||
            err.response?.data?.message ||
            "Failed to load sorted tasks. Is the backend running?"
        )
      } finally {
        setLoading(false)
      }
    }

    fetchTasks()
  }, [page, pageSize])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const currentStart = (page - 1) * pageSize + 1
  const currentEnd = Math.min(total, page * pageSize)

  return (
    <div className="page">
      <h2>Task Sorting</h2>

      {loading && <p>Loading sorted tasks…</p>}

      {error && <p style={{ color: "red" }}>{error}</p>}

      {!loading && !error && (
        <div>
          <div style={{ marginBottom: "0.8rem" }}>
            {total === 0 ? (
              <p>No tasks found. Upload a dataset first.</p>
            ) : (
              <p>
                Showing {currentStart}–{currentEnd} of {total} tasks (page {page}/{totalPages})
              </p>
            )}

            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1 || loading}>
              Previous
            </button>
            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages || loading} style={{ marginLeft: "8px" }}>
              Next
            </button>
          </div>

          {tasks.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Priority</th>
                  <th>CPU</th>
                  <th>Memory</th>
                  <th>Execution</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task, idx) => (
                  <tr key={idx}>
                    <td>{task.id}</td>
                    <td>{task.priority}</td>
                    <td>{task.cpu_request ?? "-"}</td>
                    <td>{task.memory_request ?? "-"}</td>
                    <td>{task.execution_time ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}

export default TaskSorting
