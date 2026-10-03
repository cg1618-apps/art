// Frontend: choose a stage - or, with `levels`, a stage or a whole level -
// from the roadmap, in one select.
//
// The stages are grouped under their level in roadmap order. With `levels`
// each group opens with the level itself, so a test record's target - the
// test of exactly one stage or one level - is one choice and can never be
// both. Values are lib/roadmap.js's `stage:<id>` / `goal:<id>`; '' is none.
//
//   goals        GET /api/goals: every level in order with its stages
//   value        the chosen `stage:<id>` / `goal:<id>`, or ''
//   onChange     (value) => void
//   levels       whether a whole level may be chosen
//   placeholder  the words for none
import { targetValue } from '../../lib/roadmap'
import { Select } from '../ui/primitives'

export default function RoadmapSelect({ goals, value, onChange, levels = false, placeholder = '不指定', ...rest }) {
  return (
    <Select value={value} onChange={(event) => onChange(event.target.value)} {...rest}>
      <option value="">{placeholder}</option>
      {(goals ?? []).map((goal) => (
        <optgroup key={goal.id} label={`${goal.code} ${goal.display_name}`}>
          {levels ? (
            <option value={targetValue('goal', goal.id)}>
              {goal.code} {goal.display_name}（整個等級）
            </option>
          ) : null}
          {(goal.stages ?? []).map((stage) => (
            <option key={stage.id} value={targetValue('stage', stage.id)}>
              階段 {stage.number} · {stage.display_name}
            </option>
          ))}
        </optgroup>
      ))}
    </Select>
  )
}
