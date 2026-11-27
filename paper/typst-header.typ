// Layout of tables in the PDF built with pandoc + Typst (see paper/README.md, "Converting").
// Short tables are kept whole and float to the top or bottom of a page, so text fills the space before them;
// the long Q24 table (Appendix B) stays in place and may break across pages. Cells are left-aligned, not
// justified, in a smaller font.
#show figure.where(kind: table): set figure(placement: auto)
#show <tbl:q24>: set figure(placement: none)
#show <tbl:q24>: set block(breakable: true)
#show figure.where(kind: table): set figure.caption(position: top)
#show table: set par(justify: false)
#show table: set text(size: 8.5pt)
#show table.cell: set align(left)
