// Frontend: what was (or will be) practised - one exercise, then optionally
// one of its drills. The record form and the timer's start form both pick it.
//
// Choosing another exercise clears the drill: a drill belongs to its exercise.
// The caller owns the state and loads the lists - every exercise, and the
// chosen exercise's drills.
//
//   exercises, drills        the two lists, or undefined while loading
//   exerciseId, drillId      the chosen ids as strings, '' for none
//   onChange({ exerciseId, drillId })
//   drillHint                the words under the drill select
import { Field, Select } from '../ui/primitives'

export default function ActivitySelect({ exercises, drills, exerciseId, drillId, onChange, drillHint }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Field label="練習項目">
        <Select value={exerciseId} onChange={(event) => onChange({ exerciseId: event.target.value, drillId: '' })}>
          <option value="">不指定</option>
          {(exercises ?? []).map((entry) => (
            <option key={entry.id} value={String(entry.id)}>
              {entry.display_name}
            </option>
          ))}
        </Select>
      </Field>
      <Field label="練法" hint={drillHint}>
        <Select
          value={drillId}
          onChange={(event) => onChange({ exerciseId, drillId: event.target.value })}
          disabled={exerciseId === ''}
        >
          <option value="">不指定練法</option>
          {(drills ?? []).map((drill) => (
            <option key={drill.id} value={String(drill.id)}>
              {drill.display_name}
            </option>
          ))}
        </Select>
      </Field>
    </div>
  )
}
