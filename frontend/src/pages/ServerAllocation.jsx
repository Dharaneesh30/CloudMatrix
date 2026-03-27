import {useEffect,useState} from "react"
import api from "../services/api"

function ServerAllocation(){
  const [allocations,setAllocations] = useState([])
  const [loading,setLoading] = useState(true)
  const [error,setError] = useState("")
  const [page,setPage] = useState(1)
  const [pageSize] = useState(100)
  const [total,setTotal] = useState(0)

  useEffect(()=>{
    const fetchAllocations = async () => {
      setLoading(true)
      setError("")
      try {
        const res = await api.get("/allocate-servers", {
          params: { page, page_size: pageSize }
        })
        setAllocations(res.data.allocations || [])
        setTotal(res.data.total || 0)
      } catch (err) {
        setError(err.response?.data?.error || "Failed to load allocation")
      } finally {
        setLoading(false)
      }
    }

    fetchAllocations()
  }, [page, pageSize])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const currentStart = (page - 1) * pageSize + 1
  const currentEnd = Math.min(total, page * pageSize)

  return(
    <div className="page">
      <h2>Greedy Server Allocation</h2>

      {loading && <p>Loading allocations…</p>}
      {error && <p style={{color:'red'}}>{error}</p>}

      {!loading && !error && (
        <div>
          <p>Showing {currentStart}-{currentEnd} of {total} allocations (page {page}/{totalPages})</p>
          <button onClick={()=>setPage(p => Math.max(1,p-1))} disabled={page===1}>Previous</button>
          <button onClick={()=>setPage(p => Math.min(totalPages,p+1))} disabled={page===totalPages} style={{marginLeft:'8px'}}>Next</button>

          <ul>
            {allocations.map((s,i)=>(
              <li key={i}>
                Server {s.server} → Task {s.task_id ?? s.task ?? "unknown"}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )

}

export default ServerAllocation