// Frontend: a named thing's other names.
//
// A stage and an exercise each carry three name slots and a
// `display_name` chosen from them by the server; a detail page shows the name
// as its heading and the remaining slots in a line beneath.

/** The filled name slots that are not the display name, in slot order. */
export function otherNames(entity) {
  return [entity.name_cn, entity.name_en, entity.name_alt].filter(
    (name) => name && name !== entity.display_name,
  )
}
