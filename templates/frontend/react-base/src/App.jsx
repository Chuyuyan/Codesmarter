import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './App.css'

// {{CUSTOM_IMPORTS}}

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>{{APP_NAME}}</h1>
        </header>
        <main>
          <Routes>
            {/* {{CUSTOM_ROUTES}} */}
            <Route path="/" element={<Home />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

function Home() {
  return (
    <div>
      <h2>Welcome to {{APP_NAME}}</h2>
      {/* {{CUSTOM_CONTENT}} */}
    </div>
  )
}

export default App



