// Frontend: a drill's 開始計時, on its exercise's page and on its own.
//
// Starts a stopwatch - the timer's default - with the drill attached and goes
// to /timer. With a timer already there - only one at a time - it just goes to
// /timer.
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useTimer } from '../../hooks/useTimer'
import { startPayload, STOPWATCH } from '../../lib/timer'
import { Button } from '../ui/primitives'

export default function StartTimerButton({ drill, size = 'sm' }) {
  const { timer, start } = useTimer()
  const navigate = useNavigate()
  const [starting, setStarting] = useState(false)

  async function begin() {
    if (!timer) {
      setStarting(true)
      try {
        await start(startPayload({ mode: STOPWATCH, drillId: drill.id }))
      } catch {
        // A 409 is a timer started elsewhere; /timer shows it, or the error.
      }
    }
    navigate('/timer')
  }

  return (
    <Button size={size} onClick={begin} disabled={starting} aria-label={`為「${drill.display_name}」開始計時`}>
      開始計時
    </Button>
  )
}
