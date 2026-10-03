// The single source of URL truth. Import these instead of hardcoding
// '/api/...' strings in components.
//
// Each group's `list()` is also its RESOURCE PREFIX: every read of that
// resource is a URL under it, which is what useApiMutation's `invalidate`
// matches on. There is no /api/edit write prefix as in food: art is behind
// Cloudflare Access as a whole, so reads and writes share one path.

const API = '/api'

export const endpoints = {
  // 選項: the open vocabularies every module reads. `categories()` is the
  // registry in code (key, label, description); GET list() takes ?category=.
  // DELETE remove(id) takes ?in_use=<n>, the count the page showed, and is a
  // 409 { field: 'in_use', expected, actual } when it has moved.
  options: {
    categories: () => `${API}/options/categories`,
    list: () => `${API}/options`,
    create: () => `${API}/options`,
    update: (id) => `${API}/options/${id}`,
    remove: (id) => `${API}/options/${id}`,
  },
  // 筆記. GET list() takes ?q=, and repeated ?category_id= and ?topic_id=,
  // each "any of".
  notes: {
    list: () => `${API}/notes`,
    detail: (id) => `${API}/notes/${id}`,
    create: () => `${API}/notes`,
    update: (id) => `${API}/notes/${id}`,
    remove: (id) => `${API}/notes/${id}`,
  },
  // 路線圖. GET list() is every goal in roadmap order, each with its stages
  // (numbered from 0 across the whole roadmap). DELETE remove(id) is a 409
  // { detail, stages } while the goal still has stages.
  goals: {
    list: () => `${API}/goals`,
    detail: (id) => `${API}/goals/${id}`,
    create: () => `${API}/goals`,
    update: (id) => `${API}/goals/${id}`,
    remove: (id) => `${API}/goals/${id}`,
  },
  // A stage of a goal. There is no stage list to read - the roadmap is
  // goals.list() - so list() is only the resource prefix invalidation matches.
  // PATCH update(id) may change goal_id, which moves the stage to the end of
  // its new goal unless a position is sent.
  stages: {
    list: () => `${API}/stages`,
    detail: (id) => `${API}/stages/${id}`,
    create: () => `${API}/stages`,
    update: (id) => `${API}/stages/${id}`,
    remove: (id) => `${API}/stages/${id}`,
  },
  // 練習. GET list() takes ?q=, ?stage_id=, ?topic_id= and ?no_stage=true;
  // each summary carries its stage, topics, drill count, record count and
  // total minutes. DELETE remove(id) is a 409 { detail, drills, records }
  // while drills or records still name it.
  exercises: {
    list: () => `${API}/exercises`,
    detail: (id) => `${API}/exercises/${id}`,
    create: () => `${API}/exercises`,
    update: (id) => `${API}/exercises/${id}`,
    remove: (id) => `${API}/exercises/${id}`,
  },
  // 練法: one prescribed way of doing an exercise. There is no drill list to
  // read - an exercise's detail carries its drills - so list() is only the
  // resource prefix. DELETE remove(id) is a 409 { detail, records }.
  drills: {
    list: () => `${API}/drills`,
    detail: (id) => `${API}/drills/${id}`,
    create: () => `${API}/drills`,
    update: (id) => `${API}/drills/${id}`,
    remove: (id) => `${API}/drills/${id}`,
  },
  // 紀錄. GET list() takes ?from=, ?to=, ?kind=, ?exercise_id= (directly or
  // through a drill), ?drill_id=, ?stage_id=, ?goal_id=; newest first.
  // summary() takes ?from=&to= and is [{ date, minutes, records }] per day -
  // under list() so a record write invalidates it too.
  records: {
    list: () => `${API}/records`,
    summary: () => `${API}/records/summary`,
    detail: (id) => `${API}/records/${id}`,
    create: () => `${API}/records`,
    update: (id) => `${API}/records/${id}`,
    remove: (id) => `${API}/records/${id}`,
  },
  health: () => '/health',
}

export { API }
