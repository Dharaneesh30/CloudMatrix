export default function SortButton({setTasks}){

const sortTasks = async () => {

const res = await fetch("http://localhost:5000/sort_tasks")

const data = await res.json()

setTasks(data)

}

return(
<button onClick={sortTasks}>
Sort Tasks (Divide & Conquer)
</button>
)

}