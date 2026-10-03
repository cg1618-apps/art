// Frontend: the route table.
//
// There is no route guard and no /edit prefix as in food: art is behind
// Cloudflare Access as a whole, so every page, reading or writing, is the
// owner's. Sharing will add reads under /s/... when Works lands.
import { Navigate, Route, Routes } from 'react-router-dom'

import Layout from './components/layout/Layout'
import ExerciseDetail from './pages/detail/Exercise'
import NoteDetail from './pages/detail/Note'
import StageDetail from './pages/detail/Stage'
import DrillForm from './pages/edit/DrillForm'
import ExerciseForm from './pages/edit/ExerciseForm'
import GoalForm from './pages/edit/GoalForm'
import NoteForm from './pages/edit/NoteForm'
import RecordForm from './pages/edit/RecordForm'
import StageForm from './pages/edit/StageForm'
import ExerciseLibrary from './pages/library/ExerciseLibrary'
import NoteLibrary from './pages/library/NoteLibrary'
import RecordLibrary from './pages/library/RecordLibrary'
import NotFound from './pages/NotFound'
import Options from './pages/options/Options'
import Roadmap from './pages/roadmap/Roadmap'
import Timer from './pages/timer/Timer'

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

        <Route path="/exercises" element={<ExerciseLibrary />} />
        <Route path="/exercises/new" element={<ExerciseForm />} />
        <Route path="/exercises/:id" element={<ExerciseDetail />} />
        <Route path="/exercises/:id/edit" element={<ExerciseForm />} />
        {/* A drill has no page of its own: it is read on its exercise's. */}
        <Route path="/drills/new" element={<DrillForm />} />
        <Route path="/drills/:id/edit" element={<DrillForm />} />

        {/* Nor does a record: it is read in its row on /records. */}
        <Route path="/records" element={<RecordLibrary />} />
        <Route path="/records/new" element={<RecordForm />} />
        <Route path="/records/:id/edit" element={<RecordForm />} />

        {/* One timer at a time, held by the server; its chip is in Layout. */}
        <Route path="/timer" element={<Timer />} />

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
