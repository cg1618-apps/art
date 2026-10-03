// Frontend: the route table.
//
// There is no route guard and no /edit prefix as in food: art is behind
// Cloudflare Access as a whole, so every page, reading or writing, is the
// owner's. Sharing will add reads under /s/... when Works lands.
import { Navigate, Route, Routes } from 'react-router-dom'

import Layout from './components/layout/Layout'
import NoteDetail from './pages/detail/Note'
import NoteForm from './pages/edit/NoteForm'
import NoteLibrary from './pages/library/NoteLibrary'
import NotFound from './pages/NotFound'
import Options from './pages/options/Options'

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        {/* Until a later module owns the home page. */}
        <Route path="/" element={<Navigate to="/notes" replace />} />

        <Route path="/notes" element={<NoteLibrary />} />
        <Route path="/notes/new" element={<NoteForm />} />
        <Route path="/notes/:id" element={<NoteDetail />} />
        <Route path="/notes/:id/edit" element={<NoteForm />} />
        <Route path="/options" element={<Options />} />

        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
