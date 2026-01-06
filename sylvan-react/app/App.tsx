import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import "./app.css";

// Define some simple components for the routes as an example
function Home() {
  return <h2>React Home Page</h2>;
}

function About() {
  return <h2>React About Page</h2>;
}

export default function App() {
  return (
    // Set the basename for all routes
    <BrowserRouter basename="/react">
      <nav>
        <ul>
          <li>
            {/* This will correctly link to "/react/" */}
            <Link to="/">Home</Link>
          </li>
          <li>
            {/* This will correctly link to "/react/about" */}
            <Link to="/about">About</Link>
          </li>
        </ul>
      </nav>
      <hr />
      <main>
        <Routes>
          {/* This will match "/react/" */}
          <Route path="/" element={<Home />} />
          {/* This will match "/react/about" */}
          <Route path="/about" element={<About />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
