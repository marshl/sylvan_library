import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Layout from './components/Layout';
import Search from './components/Search';
import SetList from './components/SetList';
import Decks from './components/Decks';
import "./app.css";

function Home() {
  return (
    <div>
      <h1>Welcome to Sylvan Library</h1>
      <p>
        This is a placeholder home page. You can navigate to the other pages
        using the links in the top bar.
      </p>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter basename="/react">
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/search" element={<Search />} />
          <Route path="/sets" element={<SetList />} />
          <Route path="/decks" element={<Decks />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
