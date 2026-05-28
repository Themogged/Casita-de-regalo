from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from textwrap import wrap
from unicodedata import normalize
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


def format_cop(value) -> str:
    amount = Decimal(value or 0).quantize(Decimal("1"))
    entero = int(amount)
    return f"${entero:,}".replace(",", ".")


def format_fecha(value) -> str:
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


def pedido_items_resumen(pedido) -> str:
    items = list(pedido.items.all())
    if not items:
        return "Sin items"
    return " | ".join(f"{item.producto_nombre} x{item.cantidad}" for item in items)


def pedido_unidades_totales(pedido) -> int:
    return sum(item.cantidad for item in pedido.items.all())


def pedidos_to_rows(queryset):
    rows = []
    for pedido in queryset:
        rows.append(
            [
                pedido.id,
                format_fecha(pedido.fecha),
                pedido.get_estado_display(),
                pedido_unidades_totales(pedido),
                float(Decimal(pedido.total)),
                pedido_items_resumen(pedido),
            ]
        )
    return rows


def pedidos_to_product_rows(queryset):
    productos = {}
    for pedido in queryset:
        for item in pedido.items.all():
            producto = productos.setdefault(
                item.producto_nombre,
                {
                    "pedidos": set(),
                    "unidades": 0,
                    "ingresos": Decimal("0"),
                },
            )
            producto["pedidos"].add(pedido.id)
            producto["unidades"] += item.cantidad or 0
            producto["ingresos"] += Decimal(item.subtotal())

    total_ingresos = sum(
        (producto["ingresos"] for producto in productos.values()),
        Decimal("0"),
    )
    rows = []
    for nombre, producto in sorted(
        productos.items(),
        key=lambda entry: (-entry[1]["ingresos"], entry[0]),
    ):
        unidades = producto["unidades"]
        ingresos = producto["ingresos"]
        precio_promedio = ingresos / unidades if unidades else Decimal("0")
        participacion = ingresos / total_ingresos if total_ingresos else Decimal("0")
        rows.append(
            [
                nombre,
                unidades,
                ingresos,
                precio_promedio,
                len(producto["pedidos"]),
                participacion,
            ]
        )
    return rows


def sanitize_filename_part(value: str) -> str:
    ascii_text = normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    safe = []
    for char in ascii_text.lower():
        if char.isalnum():
            safe.append(char)
        elif char in {" ", "-", "_"}:
            safe.append("-")

    filename = "".join(safe).strip("-")
    while "--" in filename:
        filename = filename.replace("--", "-")
    return filename or "archivo"


def build_filename(prefix: str, suffix: str, extension: str) -> str:
    safe_prefix = sanitize_filename_part(prefix)
    safe_suffix = sanitize_filename_part(suffix)
    return f"{safe_prefix}-{safe_suffix}.{extension}"


def pedido_to_pdf_lines(pedido, include_heading=True):
    heading = f"Pedido #{pedido.id}" if include_heading else "Resumen del pedido"
    lines = [
        (13, heading),
        f"Fecha: {format_fecha(pedido.fecha)}",
        f"Estado: {pedido.get_estado_display()}",
        f"Unidades: {pedido_unidades_totales(pedido)}",
        f"Total: {format_cop(pedido.total)}",
        "",
        (12, "Detalle de productos"),
    ]

    items = list(pedido.items.all())
    if not items:
        lines.append("Sin items registrados.")
    else:
        for item in items:
            subtotal = format_cop(item.subtotal())
            lines.append(
                f"- {item.producto_nombre}: {item.cantidad} x {format_cop(item.precio)} = {subtotal}"
            )

    return lines


def pedidos_to_pdf_lines(queryset):
    lines = []
    for pedido in queryset:
        lines.extend(pedido_to_pdf_lines(pedido))
        lines.append("")
    return lines or ["No hay pedidos para exportar."]


def _xlsx_column_letter(index: int) -> str:
    letters = []
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters.append(chr(65 + remainder))
    return "".join(reversed(letters))


def _xml_attr(value) -> str:
    return escape(str(value), {'"': "&quot;"})


def _xlsx_cell(ref: str, value, style_id: int = 0) -> str:
    style_attr = f' s="{style_id}"' if style_id else ""
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        numeric = format(Decimal(str(value)), "f")
        return f'<c r="{ref}"{style_attr}><v>{numeric}</v></c>'

    text = "" if value is None else str(value)
    safe = escape(text).replace("\r\n", "\n").replace("\r", "\n")
    return (
        f'<c r="{ref}"{style_attr} t="inlineStr"><is><t xml:space="preserve">{safe}</t></is></c>'
    )


def _xlsx_row(row_index: int, values, style_ids=None, height=None) -> str:
    style_ids = style_ids or []
    height_attr = f' ht="{height}" customHeight="1"' if height else ""
    cells = []
    for col_index, value in enumerate(values, start=1):
        ref = f"{_xlsx_column_letter(col_index)}{row_index}"
        style_id = style_ids[col_index - 1] if col_index <= len(style_ids) else 0
        cells.append(_xlsx_cell(ref, value, style_id))
    return f'<row r="{row_index}"{height_attr}>{"".join(cells)}</row>'


def _xlsx_column_width(header: str) -> int:
    normalized = normalize("NFKD", str(header)).encode("ascii", "ignore").decode("ascii").lower()
    if "items" in normalized:
        return 54
    if "producto" in normalized:
        return 42
    if "fecha" in normalized:
        return 20
    if "total" in normalized or "precio" in normalized or "subtotal" in normalized:
        return 16
    if "estado" in normalized:
        return 16
    if "unidad" in normalized or "cantidad" in normalized:
        return 12
    if "pedido" in normalized:
        return 12
    return 18


def _xlsx_data_style(header: str) -> int:
    normalized = normalize("NFKD", str(header)).encode("ascii", "ignore").decode("ascii").lower()
    if "%" in normalized or "participacion" in normalized:
        return 11
    if any(token in normalized for token in ("total", "precio", "subtotal", "venta", "ingreso")):
        return 7
    if any(token in normalized for token in ("unidad", "cantidad", "pedido")):
        return 6
    return 5


def _xlsx_styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<numFmts count="2">'
        '<numFmt numFmtId="164" formatCode="&quot;$&quot; #,##0"/>'
        '<numFmt numFmtId="165" formatCode="0.0%"/>'
        '</numFmts>'
        '<fonts count="7">'
        '<font><sz val="10"/><color rgb="FF3B1728"/><name val="Segoe UI"/></font>'
        '<font><b/><sz val="14"/><color rgb="FFFFFFFF"/><name val="Segoe UI"/></font>'
        '<font><sz val="10"/><color rgb="FFFFEAF2"/><name val="Segoe UI"/></font>'
        '<font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Segoe UI"/></font>'
        '<font><b/><sz val="10"/><color rgb="FF3B1728"/><name val="Segoe UI"/></font>'
        '<font><b/><sz val="12"/><color rgb="FF841244"/><name val="Segoe UI"/></font>'
        '<font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Segoe UI"/></font>'
        '</fonts>'
        '<fills count="8">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF841244"/><bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFD7266D"/><bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFFFF1F7"/><bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFFFEAF2"/><bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFFFFFFF"/><bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFF7EEF3"/><bgColor indexed="64"/></patternFill></fill>'
        '</fills>'
        '<borders count="2">'
        '<border><left/><right/><top/><bottom/><diagonal/></border>'
        '<border><left style="thin"><color rgb="FFF0D7E2"/></left><right style="thin"><color rgb="FFF0D7E2"/></right><top style="thin"><color rgb="FFF0D7E2"/></top><bottom style="thin"><color rgb="FFF0D7E2"/></bottom><diagonal/></border>'
        '</borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="16">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"><alignment vertical="center"/></xf>'
        '<xf numFmtId="0" fontId="2" fillId="3" borderId="0" xfId="0" applyFont="1" applyFill="1"><alignment vertical="center"/></xf>'
        '<xf numFmtId="0" fontId="4" fillId="4" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="0" fontId="3" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"><alignment vertical="top" wrapText="1"/></xf>'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="164" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyBorder="1"><alignment horizontal="right" vertical="center"/></xf>'
        '<xf numFmtId="0" fontId="4" fillId="5" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment vertical="center"/></xf>'
        '<xf numFmtId="164" fontId="4" fillId="5" borderId="1" xfId="0" applyFont="1" applyFill="1" applyNumberFormat="1" applyBorder="1"><alignment horizontal="right" vertical="center"/></xf>'
        '<xf numFmtId="0" fontId="4" fillId="5" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="165" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="0" fontId="6" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="0" fontId="5" fillId="6" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="164" fontId="5" fillId="6" borderId="1" xfId="0" applyFont="1" applyFill="1" applyNumberFormat="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="165" fontId="5" fillId="6" borderId="1" xfId="0" applyFont="1" applyFill="1" applyNumberFormat="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>'
        '</cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        '<dxfs count="0"/><tableStyles count="0" defaultTableStyle="TableStyleMedium4" defaultPivotStyle="PivotStyleLight16"/>'
        '</styleSheet>'
    )


def _summary_value_style(label: str) -> int:
    normalized = normalize("NFKD", str(label)).encode("ascii", "ignore").decode("ascii").lower()
    if "%" in normalized:
        return 15
    if "venta" in normalized or "ingreso" in normalized or "ticket" in normalized:
        return 14
    return 13


def _xlsx_table_xml(table_id: int, display_name: str, ref: str, headers) -> str:
    columns = []
    for index, header in enumerate(headers, start=1):
        columns.append(f'<tableColumn id="{index}" name="{_xml_attr(header)}"/>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<table xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'id="{table_id}" name="{display_name}" displayName="{display_name}" ref="{ref}" '
        'totalsRowShown="0">'
        f'<autoFilter ref="{ref}"/>'
        f'<tableColumns count="{len(columns)}">{"".join(columns)}</tableColumns>'
        '<tableStyleInfo name="TableStyleMedium4" showFirstColumn="0" showLastColumn="0" '
        'showRowStripes="1" showColumnStripes="0"/>'
        '</table>'
    )


def _worksheet_table_rels_xml(table_name: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/table" '
        f'Target="../tables/{table_name}.xml"/>'
        '</Relationships>'
    )


def _build_summary_sheet_xml(title, subtitle, summary, status_breakdown, top_items) -> str:
    col_count = 8
    last_col = _xlsx_column_letter(col_count)
    rows_xml = [
        _xlsx_row(1, [title] + [""] * (col_count - 1), [1] * col_count, height=24),
        _xlsx_row(2, [subtitle] + [""] * (col_count - 1), [2] * col_count, height=18),
    ]

    summary_items = list(summary or [])
    kpi_labels = []
    kpi_values = []
    kpi_value_styles = []
    for label, value in summary_items[:4]:
        kpi_labels.extend([label, ""])
        kpi_values.extend([value, ""])
        kpi_value_styles.extend([_summary_value_style(label)] * 2)
    kpi_labels.extend([""] * (col_count - len(kpi_labels)))
    kpi_values.extend([""] * (col_count - len(kpi_values)))
    kpi_value_styles.extend([13] * (col_count - len(kpi_value_styles)))
    rows_xml.append(_xlsx_row(4, kpi_labels[:col_count], [12] * col_count, height=18))
    rows_xml.append(_xlsx_row(5, kpi_values[:col_count], kpi_value_styles[:col_count], height=26))

    rows_xml.append(_xlsx_row(8, ["Estado de pedidos", "", "", "Productos destacados", "", "", "", ""], [12] * col_count, height=18))
    rows_xml.append(
        _xlsx_row(
            9,
            ["Estado", "Pedidos", "", "Producto", "Unidades", "Ingresos", "% ventas", ""],
            [4] * col_count,
            height=20,
        )
    )

    max_rows = max(len(status_breakdown or []), len(top_items or []))
    if not status_breakdown and not top_items:
        max_rows = 1
        rows_xml.append(
            _xlsx_row(
                10,
                ["Sin datos para resumir.", "", "", "Sin productos para mostrar.", "", "", "", ""],
                [5] * col_count,
                height=18,
            )
        )
    else:
        for offset in range(max_rows):
            status = (status_breakdown or [])[offset] if offset < len(status_breakdown or []) else None
            product = (top_items or [])[offset] if offset < len(top_items or []) else None
            row = [
                status["label"] if status else "",
                status["count"] if status else "",
                "",
                product["producto_nombre"] if product else "",
                product["unidades"] if product else "",
                product["ingresos"] if product else "",
                product.get("participacion", "") if product else "",
                "",
            ]
            rows_xml.append(_xlsx_row(10 + offset, row, [5, 6, 5, 5, 6, 7, 11, 5], height=18))

    dimension_ref = f"A1:{last_col}{10 + max_rows}"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetPr><tabColor rgb="FF841244"/></sheetPr>'
        f'<dimension ref="{dimension_ref}"/>'
        '<sheetViews><sheetView showGridLines="0" workbookViewId="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="18"/>'
        '<cols>'
        '<col min="1" max="1" width="20" customWidth="1"/>'
        '<col min="2" max="2" width="13" customWidth="1"/>'
        '<col min="3" max="3" width="4" customWidth="1"/>'
        '<col min="4" max="4" width="42" customWidth="1"/>'
        '<col min="5" max="5" width="13" customWidth="1"/>'
        '<col min="6" max="6" width="16" customWidth="1"/>'
        '<col min="7" max="7" width="12" customWidth="1"/>'
        '<col min="8" max="8" width="4" customWidth="1"/>'
        '</cols>'
        f'<sheetData>{"".join(rows_xml)}</sheetData>'
        '<mergeCells count="12">'
        f'<mergeCell ref="A1:{last_col}1"/>'
        f'<mergeCell ref="A2:{last_col}2"/>'
        '<mergeCell ref="A4:B4"/>'
        '<mergeCell ref="C4:D4"/>'
        '<mergeCell ref="E4:F4"/>'
        '<mergeCell ref="G4:H4"/>'
        '<mergeCell ref="A5:B5"/>'
        '<mergeCell ref="C5:D5"/>'
        '<mergeCell ref="E5:F5"/>'
        '<mergeCell ref="G5:H5"/>'
        '<mergeCell ref="A8:B8"/>'
        '<mergeCell ref="D8:G8"/>'
        '</mergeCells>'
        '<pageMargins left="0.35" right="0.35" top="0.55" bottom="0.55" header="0.2" footer="0.2"/>'
        '</worksheet>'
    )


def _build_detail_sheet_xml(
    sheet_name: str,
    headers,
    rows,
    title,
    subtitle,
    summary,
    include_table=False,
) -> str:
    sheet_rows = []
    headers = list(headers)
    rows = list(rows)
    col_count = max(len(headers), 1)
    last_col = _xlsx_column_letter(col_count)
    report_title = title or sheet_name
    report_subtitle = subtitle or "Casita de Regalos"
    summary = list(summary or [])

    sheet_rows.append(_xlsx_row(1, [report_title] + [""] * (col_count - 1), [1] * col_count, height=24))
    sheet_rows.append(_xlsx_row(2, [report_subtitle] + [""] * (col_count - 1), [2] * col_count, height=18))

    current_row = 4
    if summary:
        summary_values = []
        for label, value in summary[:3]:
            summary_values.extend([label, value])
        summary_values = summary_values[:col_count]
        summary_values.extend([""] * (col_count - len(summary_values)))
        sheet_rows.append(_xlsx_row(3, summary_values, [3] * col_count, height=20))
        current_row = 5

    header_row_index = current_row
    sheet_rows.append(_xlsx_row(header_row_index, headers, [4] * col_count, height=20))

    data_start_row = header_row_index + 1
    if rows:
        for row_index, row in enumerate(rows, start=data_start_row):
            style_ids = [_xlsx_data_style(header) for header in headers]
            sheet_rows.append(_xlsx_row(row_index, row, style_ids, height=18))
        last_data_row = data_start_row + len(rows) - 1
    else:
        sheet_rows.append(_xlsx_row(data_start_row, ["Sin pedidos para exportar."] + [""] * (col_count - 1), [5] * col_count, height=18))
        last_data_row = data_start_row

    total_row = last_data_row + 1
    if rows and "Total COP" in headers:
        total_index = headers.index("Total COP")
        unidades_index = headers.index("Unidades") if "Unidades" in headers else None
        total_values = [""] * col_count
        total_values[0] = "Total general"
        total_values[total_index] = sum(Decimal(str(row[total_index] or 0)) for row in rows)
        if unidades_index is not None:
            total_values[unidades_index] = sum(int(row[unidades_index] or 0) for row in rows)
        total_styles = [8] * col_count
        total_styles[total_index] = 9
        if unidades_index is not None:
            total_styles[unidades_index] = 10
        sheet_rows.append(_xlsx_row(total_row, total_values, total_styles, height=20))
    else:
        total_row = last_data_row

    columns = []
    for col_index, header in enumerate(headers, start=1):
        width = _xlsx_column_width(header)
        columns.append(f'<col min="{col_index}" max="{col_index}" width="{width}" customWidth="1"/>')

    merged_cells = [
        f'<mergeCell ref="A1:{last_col}1"/>',
        f'<mergeCell ref="A2:{last_col}2"/>',
    ]
    if col_count > 1 and not summary:
        merged_cells.append(f'<mergeCell ref="A3:{last_col}3"/>')

    table_ref = f"A{header_row_index}:{last_col}{last_data_row}"
    auto_filter = f'<autoFilter ref="{table_ref}"/>' if headers and not include_table else ""
    dimension_ref = f"A1:{last_col}{total_row}"
    table_namespace = ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"' if include_table else ""
    table_parts = '<tableParts count="1"><tablePart r:id="rId1"/></tableParts>' if include_table else ""

    worksheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"{table_namespace}>'
        '<sheetPr><tabColor rgb="FFD7266D"/></sheetPr>'
        f'<dimension ref="{dimension_ref}"/>'
        '<sheetViews><sheetView showGridLines="0" workbookViewId="0">'
        f'<pane ySplit="{header_row_index}" topLeftCell="A{header_row_index + 1}" activePane="bottomLeft" state="frozen"/>'
        '</sheetView></sheetViews>'
        '<sheetFormatPr defaultRowHeight="18"/>'
        f'<cols>{"".join(columns)}</cols>'
        f"<sheetData>{''.join(sheet_rows)}</sheetData>"
        f"{auto_filter}"
        f'<mergeCells count="{len(merged_cells)}">{"".join(merged_cells)}</mergeCells>'
        '<pageMargins left="0.35" right="0.35" top="0.55" bottom="0.55" header="0.2" footer="0.2"/>'
        f"{table_parts}"
        "</worksheet>"
    )
    return worksheet_xml, table_ref


def build_excel_bytes(
    sheet_name: str,
    headers,
    rows,
    title=None,
    subtitle=None,
    summary=None,
    status_breakdown=None,
    top_items=None,
    item_headers=None,
    item_rows=None,
) -> bytes:
    headers = list(headers)
    rows = list(rows)
    report_title = title or sheet_name
    report_subtitle = subtitle or "Casita de Regalos"
    summary = list(summary or [])
    status_breakdown = list(status_breakdown or [])
    top_items = list(top_items or [])
    include_item_sheet = item_headers is not None
    item_headers = list(item_headers or [])
    item_rows = list(item_rows or [])

    summary_sheet_xml = _build_summary_sheet_xml(
        report_title,
        report_subtitle,
        summary,
        status_breakdown,
        top_items,
    )
    detail_sheet_xml, pedidos_table_ref = _build_detail_sheet_xml(
        sheet_name,
        headers,
        rows,
        report_title,
        report_subtitle,
        summary,
        include_table=True,
    )
    product_sheet_xml = ""
    productos_table_ref = ""
    if include_item_sheet:
        product_sheet_xml, productos_table_ref = _build_detail_sheet_xml(
            "Productos",
            item_headers,
            item_rows,
            "Rendimiento por producto",
            report_subtitle,
            summary,
            include_table=True,
        )

    item_sheet_entry = '<sheet name="Productos" sheetId="3" r:id="rId3"/>' if include_item_sheet else ""
    item_relationship = (
        '<Relationship Id="rId3" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet3.xml"/>'
        if include_item_sheet
        else ""
    )
    styles_relationship_id = "rId4" if include_item_sheet else "rId3"
    item_content_type = (
        '<Override PartName="/xl/worksheets/sheet3.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        if include_item_sheet
        else ""
    )
    product_table_content_type = (
        '<Override PartName="/xl/tables/table2.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.table+xml"/>'
        if include_item_sheet
        else ""
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<bookViews><workbookView/></bookViews>'
        '<sheets>'
        '<sheet name="Panel" sheetId="1" r:id="rId1"/>'
        f'<sheet name="{_xml_attr(sheet_name)}" sheetId="2" r:id="rId2"/>'
        f"{item_sheet_entry}"
        '</sheets>'
        "</workbook>"
    )

    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet2.xml"/>'
        f"{item_relationship}"
        f'<Relationship Id="{styles_relationship_id}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
        "</Relationships>"
    )

    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/worksheets/sheet2.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        f"{item_content_type}"
        '<Override PartName="/xl/tables/table1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.table+xml"/>'
        f"{product_table_content_type}"
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        "</Types>"
    )

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/styles.xml", _xlsx_styles_xml())
        archive.writestr("xl/worksheets/sheet1.xml", summary_sheet_xml)
        archive.writestr("xl/worksheets/sheet2.xml", detail_sheet_xml)
        archive.writestr(
            "xl/worksheets/_rels/sheet2.xml.rels",
            _worksheet_table_rels_xml("table1"),
        )
        archive.writestr(
            "xl/tables/table1.xml",
            _xlsx_table_xml(1, "TablaPedidos", pedidos_table_ref, headers),
        )
        if include_item_sheet:
            archive.writestr("xl/worksheets/sheet3.xml", product_sheet_xml)
            archive.writestr(
                "xl/worksheets/_rels/sheet3.xml.rels",
                _worksheet_table_rels_xml("table2"),
            )
            archive.writestr(
                "xl/tables/table2.xml",
                _xlsx_table_xml(2, "TablaProductos", productos_table_ref, item_headers),
            )

    return buffer.getvalue()


def _pdf_safe(text: str) -> str:
    ascii_text = normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    return (
        ascii_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    )


def build_pdf_bytes(title: str, subtitle: str, lines) -> bytes:
    page_width = 612
    page_height = 792
    margin_left = 52
    margin_right = 52
    content_top = 662
    margin_bottom = 72

    def rect_command(x, y, width, height, color):
        return f"q {color} rg {x} {y} {width} {height} re f Q"

    def text_command(font, size, x, y, text, color="0.231 0.090 0.157"):
        return (
            f"BT {color} rg /{font} {size} Tf 1 0 0 1 {x} {y} Tm "
            f"({_pdf_safe(text)}) Tj ET"
        )

    prepared_lines = []
    for line in lines:
        if isinstance(line, tuple):
            size, text = line
        else:
            size, text = 11, line

        if not str(text).strip():
            prepared_lines.append(("space", size, ""))
            continue

        kind = "heading" if size >= 12 else "text"
        wrap_width = 66 if kind == "heading" else 88
        chunks = wrap(str(text), width=wrap_width) or [""]
        for chunk in chunks:
            prepared_lines.append((kind, size, chunk))

    if not prepared_lines:
        prepared_lines.append(("text", 11, "No hay datos para mostrar."))

    pages = []
    current_page = []
    current_y = content_top

    for kind, size, text in prepared_lines:
        if kind == "space":
            line_height = 10
        elif kind == "heading":
            line_height = 28
        else:
            line_height = 17
        if current_y - line_height < margin_bottom:
            pages.append(current_page)
            current_page = []
            current_y = content_top
        current_page.append((kind, size, margin_left, current_y, text))
        current_y -= line_height

    if current_page:
        pages.append(current_page)

    objects = [None, None]
    font_regular_id = 3
    font_bold_id = 4
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    page_ids = []
    total_pages = len(pages)

    for page_number, page in enumerate(pages, start=1):
        commands = [
            rect_command(0, 0, page_width, page_height, "1 0.988 0.996"),
            rect_command(0, 706, page_width, 86, "0.518 0.071 0.267"),
            rect_command(0, 700, page_width, 6, "0.843 0.149 0.427"),
            rect_command(42, 52, page_width - 84, 626, "1 1 1"),
            rect_command(42, 52, 4, 626, "1 0.918 0.949"),
            text_command("F2", 9, 52, 760, "CASITA DE REGALOS", "1 0.918 0.949"),
            text_command("F2", 20, 52, 735, title, "1 1 1"),
            text_command("F1", 10, 52, 716, subtitle, "1 0.918 0.949"),
        ]

        for kind, size, x, y, text in page:
            if kind == "space":
                continue
            if kind == "heading":
                commands.append(rect_command(52, y - 7, page_width - 104, 22, "1 0.945 0.969"))
                commands.append(text_command("F2", min(size, 13), x + 8, y, text, "0.518 0.071 0.267"))
            else:
                commands.append(text_command("F1", min(size, 11), x + 8, y, text))

        commands.extend(
            [
                rect_command(42, 42, page_width - 84, 1, "0.941 0.843 0.886"),
                text_command("F1", 8, 42, 28, "Generado por Casita de Regalos", "0.451 0.314 0.392"),
                text_command(
                    "F1",
                    8,
                    page_width - 112,
                    28,
                    f"Pagina {page_number} de {total_pages}",
                    "0.451 0.314 0.392",
                ),
            ]
        )

        stream = "\n".join(commands).encode("latin-1")
        content_id = len(objects) + 1
        objects.append(
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )
        page_id = len(objects) + 1
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
                f"/Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_bold_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[1] = f"<< /Type /Pages /Count {len(page_ids)} /Kids [{kids}] >>".encode(
        "ascii"
    )

    buffer = BytesIO()
    buffer.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]

    for index, obj in enumerate(objects, start=1):
        offsets.append(buffer.tell())
        buffer.write(f"{index} 0 obj\n".encode("ascii"))
        buffer.write(obj)
        buffer.write(b"\nendobj\n")

    xref_start = buffer.tell()
    buffer.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.write(f"{offset:010d} 00000 n \n".encode("ascii"))

    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF"
    )
    buffer.write(trailer.encode("ascii"))
    return buffer.getvalue()
