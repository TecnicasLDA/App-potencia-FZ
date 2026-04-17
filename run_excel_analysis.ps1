$ErrorActionPreference='Stop'
$file = "C:\Users\jaruani\Downloads\Python\App de potencia\GRAFICOS DE POTENCIAS 2026-MARZO.xlsx"
$xlCellTypeFormulas = -4123
$xlRowField = 1
$xlColumnField = 2
$xlPageField = 3
$xlDataField = 4
$keywords = @('POT_DEMANDADA','POT_FACT_PUNTA','POT_FACT_VALLE','POT_FACT_LLANO','MAX','NIC','COMBINACION','SECTOR','BUSCARV','XLOOKUP','INDEX','MATCH','INDICE','COINCIDIR','FILTRAR')

$result = [ordered]@{
  File=$file; COMAvailable=$false; Sheets=@(); Tables=@(); Pivots=@();
  FormulaHits=@(); RepresentativeFormulas=@(); NicReferenceTables=@(); Limitation=$null
}
$excel = $null
$wb = $null

try {
  $excel = New-Object -ComObject Excel.Application
  $result.COMAvailable = $true
  $excel.Visible = $false
  $excel.DisplayAlerts = $false
  $wb = $excel.Workbooks.Open($file,0,$true)

  $allFormulaRows = New-Object System.Collections.Generic.List[object]

  foreach ($ws in $wb.Worksheets) {
    $used = $ws.UsedRange
    $result.Sheets += [pscustomobject]@{ Sheet=$ws.Name; UsedRows=[int]$used.Rows.Count; UsedColumns=[int]$used.Columns.Count }

    foreach ($lo in $ws.ListObjects) {
      $headers = @()
      if ($lo.HeaderRowRange -ne $null) {
        foreach ($c in $lo.HeaderRowRange.Cells) { $headers += [string]$c.Value2 }
      }
      $result.Tables += [pscustomobject]@{ Sheet=$ws.Name; Name=$lo.Name; Range=$lo.Range.Address($false,$false); HeaderColumns=$headers }
    }

    foreach ($pt in $ws.PivotTables()) {
      $rowFields = @(); $colFields = @(); $dataFields = @(); $filterFields = @()
      foreach ($pf in $pt.PivotFields()) {
        $n = [string]$pf.Name
        switch ([int]$pf.Orientation) {
          1 { $rowFields += $n }
          2 { $colFields += $n }
          3 { $filterFields += $n }
          4 { $dataFields += $n }
        }
      }
      $result.Pivots += [pscustomobject]@{
        Sheet=$ws.Name; Name=$pt.Name; TableRange=$pt.TableRange2.Address($false,$false); SourceData=[string]$pt.SourceData;
        RowFields=$rowFields; ColumnFields=$colFields; DataFields=$dataFields; FilterFields=$filterFields
      }
    }

    try {
      $fCells = $used.SpecialCells($xlCellTypeFormulas)
      foreach ($cell in $fCells.Cells) {
        $f = [string]$cell.Formula
        if ([string]::IsNullOrWhiteSpace($f)) { continue }
        $hitKeywords = @()
        foreach ($k in $keywords) { if ($f -match [regex]::Escape($k)) { $hitKeywords += $k } }
        $row = [pscustomobject]@{ Sheet=$ws.Name; Cell=$cell.Address($false,$false); Formula=$f; Hits=$hitKeywords }
        $allFormulaRows.Add($row)
        if ($hitKeywords.Count -gt 0) { $result.FormulaHits += $row }
      }
    } catch {}
  }

  $result.RepresentativeFormulas = $allFormulaRows | Select-Object -First 20

  $nicCols = @('NIC','N° NIC','Nº NIC','SECTOR','DENOMINACION','TARIFA','COMBINACION','SECTOR MACRO')
  foreach ($t in $result.Tables) {
    $headersUpper = @($t.HeaderColumns | ForEach-Object { ([string]$_).ToUpperInvariant().Trim() })
    $score = 0
    foreach ($needle in $nicCols) { if ($headersUpper -contains $needle.ToUpperInvariant()) { $score++ } }
    if ($score -ge 2) {
      $formulaUses = @($result.FormulaHits | Where-Object {
        $_.Formula -match [regex]::Escape($t.Name) -or (($_.Formula -match 'NIC') -and ($_.Formula -match 'SECTOR|COMBINACION|TARIFA|DENOMINACION'))
      } | Select-Object -First 10)
      $pivotUses = @($result.Pivots | Where-Object {
        $_.SourceData -match [regex]::Escape($t.Name) -or (($_.RowFields + $_.ColumnFields + $_.DataFields + $_.FilterFields) -match 'NIC|SECTOR|COMBINACION|TARIFA|DENOMINACION')
      } | Select-Object -First 10)
      $result.NicReferenceTables += [pscustomobject]@{
        Sheet=$t.Sheet; Name=$t.Name; Range=$t.Range; HeaderColumns=$t.HeaderColumns; FormulaUsage=$formulaUses; PivotUsage=$pivotUses
      }
    }
  }
}
catch {
  $result.Limitation = "Excel COM no disponible o no se pudo abrir en solo lectura: $($_.Exception.Message)"
}
finally {
  if ($wb -ne $null) { $wb.Close($false) | Out-Null }
  if ($excel -ne $null) { $excel.Quit() | Out-Null }
  [System.GC]::Collect()
  [System.GC]::WaitForPendingFinalizers()
}

$result | ConvertTo-Json -Depth 8 | Set-Content -Path ".\analisis_excel_com.json" -Encoding UTF8

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("Archivo: $($result.File)")
$lines.Add("COM disponible: $($result.COMAvailable)")
if ($result.Limitation) { $lines.Add("Limitación: $($result.Limitation)") }
$lines.Add("`n1) Hojas y UsedRange:")
foreach ($s in $result.Sheets) { $lines.Add("- $($s.Sheet): filas=$($s.UsedRows), columnas=$($s.UsedColumns)") }
$lines.Add("`n2) Tablas (ListObjects):")
if ($result.Tables.Count -eq 0) { $lines.Add("- No se encontraron tablas.") } else { foreach ($t in $result.Tables) { $lines.Add("- Hoja $($t.Sheet) | Tabla $($t.Name) | Rango $($t.Range)") } }
$lines.Add("`n3) Tablas dinámicas (PivotTables):")
if ($result.Pivots.Count -eq 0) { $lines.Add("- No se encontraron tablas dinámicas.") } else {
  foreach ($p in $result.Pivots) {
    $lines.Add("- Hoja $($p.Sheet) | Pivot $($p.Name) | Rango $($p.TableRange)")
    $lines.Add("  Row: $([string]::Join(', ', $p.RowFields))")
    $lines.Add("  Column: $([string]::Join(', ', $p.ColumnFields))")
    $lines.Add("  Data: $([string]::Join(', ', $p.DataFields))")
    $lines.Add("  Filter: $([string]::Join(', ', $p.FilterFields))")
  }
}
$lines.Add("`n4) Coincidencias de fórmulas por palabras clave:")
if ($result.FormulaHits.Count -eq 0) { $lines.Add("- No se encontraron coincidencias.") } else {
  $grouped = $result.FormulaHits | ForEach-Object { $_.Hits } | Group-Object | Sort-Object Count -Descending
  foreach ($g in $grouped) { $lines.Add("- $($g.Name): $($g.Count)") }
}
$lines.Add("`n5) 20 fórmulas representativas:")
foreach ($f in $result.RepresentativeFormulas) { $lines.Add("- $($f.Sheet)!$($f.Cell) => $($f.Formula)") }
$lines.Add("`n6) Segmentación NIC por tablas de referencia:")
if ($result.NicReferenceTables.Count -eq 0) {
  $lines.Add("- No se identificaron tablas de referencia NIC con suficientes columnas clave.")
} else {
  foreach ($n in $result.NicReferenceTables) {
    $lines.Add("- Hoja $($n.Sheet) | Tabla $($n.Name) | Rango $($n.Range)")
    $lines.Add("  Columnas: $([string]::Join(', ', $n.HeaderColumns))")
    if ($n.FormulaUsage.Count -gt 0) {
      $lines.Add("  Uso en fórmulas (muestra):")
      foreach ($fu in $n.FormulaUsage) { $lines.Add("    * $($fu.Sheet)!$($fu.Cell): $($fu.Formula)") }
    } else { $lines.Add("  Uso en fórmulas: sin evidencia directa en la muestra.") }
    if ($n.PivotUsage.Count -gt 0) {
      $lines.Add("  Uso en pivots (muestra):")
      foreach ($pu in $n.PivotUsage) { $lines.Add("    * $($pu.Sheet) | $($pu.Name) | Source: $($pu.SourceData)") }
    } else { $lines.Add("  Uso en pivots: sin evidencia directa en la muestra.") }
  }
}
$lines | Set-Content -Path ".\analisis_excel_com_resumen.txt" -Encoding UTF8
