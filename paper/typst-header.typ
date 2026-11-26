// Layout of tables in the PDF built with pandoc + Typst (see paper/README.md, "Converting").
// Long tables may break across pages; cells are left-aligned, not justified, in a smaller font.
#show figure: set block(breakable: true)
#show figure.where(kind: table): set figure.caption(position: top)
#show table: set par(justify: false)
#show table: set text(size: 8.5pt)
#show table.cell: set align(left)
