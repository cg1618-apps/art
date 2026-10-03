// Frontend: a record's fields, apart from its date and minutes - the record
// form's (pages/edit/RecordForm) and the timer's record draft's
// (pages/timer/Timer), so the two cannot drift.
//
// In reading order: the location (under `when`, the date and minutes, when the
// caller has them - the timer's are its own), what was practised, the kind and
// a test's target, the method, the tool, the reference rows, the notes. Each
// section is the record form's as it was; lib/records.js holds the rules
// (UNCHOSEN defaults, one activity, a test's one target).
//
//   form, setForm   the record form's state (lib/records.js) and its setter
//   defaults        { location_id, tool_id } for fields still UNCHOSEN
//   when            the date and minutes fields, or nothing
//
// The lists it picks from are loaded here; the caller loads only what it needs
// to decide whether it can save.
import { endpoints } from '../../api/endpoints'
import { useApiQuery, useOptions } from '../../hooks/useApi'
import { chosen, RECORD_KINDS, TEST_KIND } from '../../lib/records'
import { Field, Section, Select, TextArea } from '../ui/primitives'
import ActivitySelect from './ActivitySelect'
import OptionPicker from './OptionPicker'
import ResourceRows from './ResourceRows'
import RoadmapSelect from './RoadmapSelect'

export default function RecordFields({ form, setForm, defaults, when = null }) {
  const exercises = useApiQuery(endpoints.exercises.list())
  const goals = useApiQuery(endpoints.goals.list())
  const locations = useOptions('location')
  const methods = useOptions('method')
  const tools = useOptions('tool')
  const exercise = useApiQuery(endpoints.exercises.detail(form.exercise_id), null, {
    enabled: form.exercise_id !== '',
  })

  const set = (field) => (event) => setForm((previous) => ({ ...previous, [field]: event.target.value }))
  const setValue = (field) => (value) => setForm((previous) => ({ ...previous, [field]: value }))

  function setActivity({ exerciseId, drillId }) {
    setForm((previous) => ({ ...previous, exercise_id: exerciseId, drill_id: drillId }))
  }

  const location = (
    <div className="space-y-1">
      <p className="text-sm font-medium text-text-muted">地點</p>
      <OptionPicker
        label="地點"
        options={locations.data}
        value={chosen(form.location_id, defaults.location_id)}
        onChange={setValue('location_id')}
      />
    </div>
  )

  return (
    <>
      <Section title={when ? '時間地點' : '地點'}>
        {when ? (
          <div className="space-y-3">
            {when}
            {location}
          </div>
        ) : (
          location
        )}
      </Section>

      <Section title="練了什麼">
        <ActivitySelect
          exercises={exercises.data}
          drills={exercise.data?.drills ?? []}
          exerciseId={form.exercise_id}
          drillId={form.drill_id}
          onChange={setActivity}
          drillHint="可以只記練習項目。"
        />
      </Section>

      <Section title="類型">
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="類型">
            <Select value={form.kind} onChange={set('kind')}>
              {RECORD_KINDS.map((kind) => (
                <option key={kind.value} value={kind.value}>
                  {kind.label}
                </option>
              ))}
            </Select>
          </Field>
          {form.kind === TEST_KIND ? (
            <Field label="測驗對象" hint="一個階段，或一整個等級。">
              <RoadmapSelect
                goals={goals.data}
                value={form.target}
                onChange={setValue('target')}
                levels
                placeholder="選擇階段或等級…"
              />
            </Field>
          ) : null}
        </div>
      </Section>

      <Section title="方法">
        <OptionPicker label="方法" options={methods.data} value={form.method_id} onChange={setValue('method_id')} />
      </Section>

      <Section title="工具">
        <OptionPicker
          label="工具"
          options={tools.data}
          value={chosen(form.tool_id, defaults.tool_id)}
          onChange={setValue('tool_id')}
        />
      </Section>

      <Section title="參考">
        <ResourceRows rows={form.references} onChange={setValue('references')} noun="參考" />
      </Section>

      <Section title="筆記">
        <Field label="筆記">
          <TextArea rows={4} value={form.notes} onChange={set('notes')} />
        </Field>
      </Section>
    </>
  )
}
