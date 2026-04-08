export default function AllocateButton(){

const allocate = async () => {

const res = await fetch("http://localhost:5000/allocate_tasks")

const data = await res.json()

console.log(data)

alert("Tasks allocated to servers")

}

return(
<button onClick={allocate}>
Allocate Tasks (Greedy)
</button>
)

}