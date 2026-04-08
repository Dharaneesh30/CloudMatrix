import { useState } from "react"

export default function ServerLoad(){

const [allocation,setAllocation] = useState([])

const fetchAllocation = async () => {

const res = await fetch("http://localhost:5000/allocate_tasks")

const data = await res.json()

setAllocation(data)

}

return(

<div>

<h3>Server Allocation Dashboard</h3>

<button onClick={fetchAllocation}>
Show Server Allocation
</button>

<table border="1">

<thead>

<tr>
<th>Task</th>
<th>Server</th>
</tr>

</thead>

<tbody>

{allocation.map((item,index)=>(
<tr key={index}>
<td>{item.task_id}</td>
<td>{item.server}</td>
</tr>
))}

</tbody>

</table>

</div>

)

}