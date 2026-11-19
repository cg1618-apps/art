# Notes are one table, filed by an option

Terms, knowledge, tips and advice are one `note` table with a `note_category`
option. Nothing behaves differently for a 名詞 than for a 小技巧, so the
category files a note and nothing more, and a new category is a row. The
glossary is Notes filtered to 名詞, and a note's `summary` is its definition
when it is a term.

Rejected: four tables, and a category held as a code enum.

Notes about one tool belong to the Tool module and a record's notes to the
record; Notes holds what is tied to neither.
