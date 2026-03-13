import TaskForm from "./components/TaskForm"
import TaskList from "./components/TaskList"
import SortButton from "./components/SortButton"
import "./App.css"

function App() {

  return (

    <div className="app-container">

      {/* HEADER */}
      <header className="header">
        <h1>CloudMatrix</h1>
        <p>AI-Based Cloud Resource Allocation And Load Balancing System</p>
      </header>

      {/* MAIN CONTENT */}
      <main className="main-content">

        <h2>Divide & Conquer - Task Priority Sorting</h2>

        <TaskForm />
        <SortButton />
        <TaskList />

      </main>

      {/* FOOTER */}
      <footer className="footer">
        © 2026 CloudMatrix | Team Project
      </footer>

    </div>
  )
}

export default App