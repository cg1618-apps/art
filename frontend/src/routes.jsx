// Frontend: the route table.
//
// There is no route guard and no /edit prefix as in food: art is behind
// Cloudflare Access as a whole, so every page, reading or writing, is the
// owner's. Sharing will add reads under /s/... when Works lands.
import { Navigate, Route, Routes } from 'react-router-dom'

import Layout from './components/layout/Layout'
import NoteDetail from './pages/detail/Note'
import StageDetail from './pages/detail/Stage'
import GoalForm from './pages/edit/GoalForm'
import NoteForm from './pages/edit/NoteForm'
import StageForm from './pages/edit/StageForm'
import NoteLibrary from './pages/library/NoteLibrary'
import NotFound from './pages/NotFound'
import Options from './pages/options/Options'
import Roadmap from './pages/roadmap/Roadmap'

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        {/* The roadmap is where a session starts: what is being worked on now. */}
        <Route path="/" element={<Navigate to="/roadmap" replace />} />

        <Route path="/roadmap" element={<Roadmap />} />
        <Route path="/roadmap/goals/new" element={<GoalForm />} />
        <Route path="/roadmap/goals/:id/edit" element={<GoalForm />} />
        <Route path="/roadmap/stages/new" element={<StageForm />} />
        <Route path="/roadmap/stages/:id" element={<StageDetail />} />
        <Route path="/roadmap/stages/:id/edit" element={<StageForm />} />

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
