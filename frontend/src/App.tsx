import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { NavBar } from './components/NavBar'
import { HomePage } from './pages/HomePage'
import { SearchPage } from './pages/SearchPage'
import { ArchivePage } from './pages/ArchivePage'

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/archive" element={<ArchivePage />} />
      </Routes>
    </BrowserRouter>
  )
}
