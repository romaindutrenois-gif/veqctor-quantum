-- Give every table explicit relative column widths, so long cells wrap instead of running off the page.
-- Width of a column ~ sqrt of its longest cell (in characters), normalised to the text width.
local function cell_len(cell)
  return #pandoc.utils.stringify(cell.contents)
end

function Table(tbl)
  local n = #tbl.colspecs
  local longest = {}
  for i = 1, n do longest[i] = 4 end
  local function scan(rows)
    for _, row in ipairs(rows) do
      for i, cell in ipairs(row.cells) do
        if i <= n then longest[i] = math.max(longest[i], cell_len(cell)) end
      end
    end
  end
  scan(tbl.head.rows)
  for _, body in ipairs(tbl.bodies) do scan(body.body) end
  local total = 0
  for i = 1, n do longest[i] = math.sqrt(longest[i]); total = total + longest[i] end
  for i = 1, n do tbl.colspecs[i] = { tbl.colspecs[i][1], 0.98 * longest[i] / total } end
  return tbl
end
