// Frontend: any path no route claims. Said plainly, with the way back, rather
// than silently redirected - a mistyped link should look like one.
import { LinkButton } from '../components/ui/primitives'
import { Empty } from '../components/ui/states'

export default function NotFound() {
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">找不到這一頁</h1>
      <Empty
        action={
          <LinkButton kind="primary" to="/notes">
            回到筆記
          </LinkButton>
        }
      >
        這個網址沒有對應的頁面。
      </Empty>
    </div>
  )
}
