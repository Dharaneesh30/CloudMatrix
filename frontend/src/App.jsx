import {BrowserRouter,Routes,Route,Link} from "react-router-dom"

import Dashboard from "./pages/Dashboard"
import TaskSorting from "./pages/TaskSorting"
import ServerAllocation from "./pages/ServerAllocation"

import "./App.css"

function App(){

return(

<BrowserRouter>

<header className="header">

<h1>CloudMatrix</h1>

<nav className="nav">

<Link to="/">Upload Dataset</Link>
<Link to="/task-sorting">Task Sorting</Link>
<Link to="/server-allocation">Server Allocation</Link>

</nav>

</header>

<Routes>

<Route path="/" element={<Dashboard/>}/>
<Route path="/task-sorting" element={<TaskSorting/>}/>
<Route path="/server-allocation" element={<ServerAllocation/>}/>

</Routes>

</BrowserRouter>

)

}

export default App