import { useState } from "react"
import { useNavigate } from "react-router-dom"
import api from "../services/api"

function UploadDataset(){

const [file,setFile] = useState(null)
const navigate = useNavigate()

const uploadDataset = async () => {

const formData = new FormData()
formData.append("file",file)

await api.post("/upload-dataset",formData)

navigate("/add-tasks")

}

return(

<div className="page">

<h2>Upload Cloud Task Dataset</h2>

<input
type="file"
onChange={(e)=>setFile(e.target.files[0])}
/>

<button onClick={uploadDataset}>
Upload Dataset
</button>

</div>

)

}

export default UploadDataset