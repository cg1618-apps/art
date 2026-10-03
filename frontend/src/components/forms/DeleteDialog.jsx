// Frontend: the one delete dialog.
//
// food's DeleteDialog in its chrome and its words (保留 / 刪除), generalised the
// other way round: food looks a kind up in a table and fetches its cascade
// counts; here the caller says what will happen and does the delete, because
// art's two deletes are a note (nothing to count) and an option (whose count
// the page already shows).
//
// A 409 carrying `field` / `actual` (the stale-count refusal) is handed to
// `onStale(actual)`, so the caller can correct the number the dialog states;
// the server's sentence is shown and the button re-offered as 確認刪除 - no
// reload. While the delete is on its way the dialog cannot be dismissed.
//
//   title      the question, e.g. 刪除筆記「透視」？
//   children   what will happen, in words
//   onConfirm  async () => void; throws to refuse
//   onStale    (actual) => void, optional
//   onClose    () => void
import { useState } from 'react'

import Dialog from '../ui/Dialog'
import { Button } from '../ui/primitives'
import { ErrorNote } from '../ui/states'

export default function DeleteDialog({ title, children, onConfirm, onStale, onClose }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function remove() {
    setBusy(true)
    setError(null)
    try {
      await onConfirm()
    } catch (caught) {
      if (caught.status === 409 && caught.body?.field && caught.body.actual !== undefined) {
        onStale?.(caught.body.actual)
      }
      setError(caught)
      setBusy(false)
    }
  }

  return (
    <Dialog
      title={title}
      onClose={onClose}
      busy={busy}
      footer={
        <>
          <Button onClick={onClose} disabled={busy}>
            保留
          </Button>
          <Button kind="danger" onClick={remove} disabled={busy}>
            {busy ? '刪除中…' : error?.body?.field ? '確認刪除' : '刪除'}
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-text">
        {children}
        {error ? <ErrorNote error={error} /> : null}
      </div>
    </Dialog>
  )
}
