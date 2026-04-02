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
                pedido.estado,
                pedido_unidades_totales(pedido),
                float(Decimal(pedido.total)),
                pedido_items_resumen(pedido),
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


def pedido_to_pdf_lines(pedido):
    lines = [
        (13, f"Pedido #{pedido.id}"),
        f"Fecha: {format_fecha(pedido.fecha)}",
        f"Estado: {pedido.get_estado_display()}",
        f"Total: {format_cop(pedido.total)}",
        "",
        (12, "Items"),
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


def _xlsx_cell(ref: str, value) -> str:
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return f'<c r="{ref}"><v>{value}</v></c>'

    text = "" if value is None else str(value)
    safe = escape(text).replace("\r\n", "\n").replace("\r", "\n")
    return (
        f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{safe}</t></is></c>'
    )


def build_excel_bytes(sheet_name: str, headers, rows) -> bytes:
    sheet_rows = []
    all_rows = [headers] + list(rows)

    for row_index, row in enumerate(all_rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            ref = f"{_xlsx_column_letter(col_index)}{row_index}"
            cells.append(_xlsx_cell(ref, value))
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    worksheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(sheet_rows)}</sheetData>"
        "</worksheet>"
    )

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{escape(sheet_name)}" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )

    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
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
        "</Types>"
    )

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet_xml)

    return buffer.getvalue()


def _pdf_safe(text: str) -> str:
    ascii_text = normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    return (
        ascii_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    )


def build_pdf_bytes(title: str, subtitle: str, lines) -> bytes:
    page_width = 612
    page_height = 792
    margin_left = 42
    margin_top = 752
    margin_bottom = 52

    prepared_lines = [(18, title), (11, subtitle), (11, "")]
    for line in lines:
        if isinstance(line, tuple):
            size, text = line
        else:
            size, text = 11, line

        chunks = wrap(str(text), width=92) or [""]
        for chunk in chunks:
            prepared_lines.append((size, chunk))

    pages = []
    current_page = []
    current_y = margin_top

    for size, text in prepared_lines:
        line_height = 24 if size >= 16 else 16
        if current_y - line_height < margin_bottom:
            pages.append(current_page)
            current_page = []
            current_y = margin_top
        current_page.append((size, margin_left, current_y, text))
        current_y -= line_height

    if current_page:
        pages.append(current_page)

    objects = [None, None]
    font_id = 3
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids = []

    for page in pages:
        commands = []
        for size, x, y, text in page:
            commands.append(
                f"BT /F1 {size} Tf 1 0 0 1 {x} {y} Tm ({_pdf_safe(text)}) Tj ET"
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
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
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
