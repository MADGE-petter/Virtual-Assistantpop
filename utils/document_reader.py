import os
from typing import Tuple


def read_text_file(file_path: str, max_chars: int = 25000) -> Tuple[bool, str, str]:
    """Read plain text and code files (.txt, .md, .py, .json, .csv, .xml, etc.)."""
    encodings = ["utf-8", "utf-8-sig", "utf-16", "cp1258", "cp1252", "latin-1"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc, errors="replace") as f:
                content = f.read(max_chars + 100)
                if len(content) > max_chars:
                    content = content[:max_chars] + "\n\n[...Nội dung đã được cắt bớt do vượt quá giới hạn tối đa...]"
                return True, content, ""
        except Exception:
            continue
    return False, "", "Không thể giải mã nội dung tệp văn bản này."


def read_docx_file(file_path: str, max_chars: int = 25000) -> Tuple[bool, str, str]:
    """Read Microsoft Word (.docx) file."""
    try:
        import docx
        doc = docx.Document(file_path)
        parts = []

        # Read paragraphs
        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                parts.append(text)

        # Read tables if any
        for table in doc.tables:
            table_lines = []
            for row in table.rows:
                cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                if any(cells):
                    table_lines.append(" | ".join(cells))
            if table_lines:
                parts.append("\n[Bảng dữ liệu]\n" + "\n".join(table_lines))

        full_text = "\n\n".join(parts)
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "\n\n[...Nội dung đã được cắt bớt do vượt quá giới hạn tối đa...]"
        return True, full_text, ""
    except Exception as e:
        return False, "", f"Lỗi đọc file Word: {e}"


def read_excel_file(file_path: str, max_chars: int = 25000) -> Tuple[bool, str, str]:
    """Read Microsoft Excel (.xlsx, .xls) file."""
    try:
        ext = os.path.splitext(file_path)[1].lower()
        parts = []

        if ext == ".xlsx":
            import openpyxl
            wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                rows_text = []
                for row_idx, row in enumerate(sheet.iter_rows(values_only=True)):
                    if row_idx > 200:  # Cap at 200 rows per sheet
                        rows_text.append("[...đã giới hạn số dòng của trang tính...]")
                        break
                    row_vals = [str(v) if v is not None else "" for v in row]
                    if any(row_vals):
                        rows_text.append(" | ".join(row_vals))
                if rows_text:
                    parts.append(f"### Sheet: {sheet_name}\n" + "\n".join(rows_text))
            wb.close()

        elif ext == ".xls":
            import xlrd
            wb = xlrd.open_workbook(file_path)
            for sheet_idx in range(wb.nsheets):
                sheet = wb.sheet_by_index(sheet_idx)
                rows_text = []
                for row_idx in range(min(sheet.nrows, 200)):
                    row_vals = [str(sheet.cell_value(row_idx, col_idx)) for col_idx in range(sheet.ncols)]
                    if any(row_vals):
                        rows_text.append(" | ".join(row_vals))
                if rows_text:
                    parts.append(f"### Sheet: {sheet.name}\n" + "\n".join(rows_text))

        full_text = "\n\n".join(parts)
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "\n\n[...Nội dung đã được cắt bớt do vượt quá giới hạn tối đa...]"
        return True, full_text, ""
    except Exception as e:
        return False, "", f"Lỗi đọc file Excel: {e}"


def read_pptx_file(file_path: str, max_chars: int = 25000) -> Tuple[bool, str, str]:
    """Read Microsoft PowerPoint (.pptx) file."""
    try:
        import pptx
        prs = pptx.Presentation(file_path)
        slides_text = []

        for idx, slide in enumerate(prs.slides, 1):
            slide_parts = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        txt = paragraph.text.strip()
                        if txt:
                            slide_parts.append(txt)
            if slide_parts:
                slides_text.append(f"### Slide {idx}:\n" + "\n".join(slide_parts))

        full_text = "\n\n".join(slides_text)
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "\n\n[...Nội dung đã được cắt bớt do vượt quá giới hạn tối đa...]"
        return True, full_text, ""
    except Exception as e:
        return False, "", f"Lỗi đọc file PowerPoint: {e}"


def read_pdf_file(file_path: str, max_chars: int = 25000) -> Tuple[bool, str, str]:
    """Read PDF (.pdf) file."""
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        pages_text = []

        for idx, page in enumerate(reader.pages, 1):
            txt = page.extract_text()
            if txt and txt.strip():
                pages_text.append(f"--- Trang {idx} ---\n{txt.strip()}")
            if sum(len(p) for p in pages_text) > max_chars:
                break

        full_text = "\n\n".join(pages_text)
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "\n\n[...Nội dung đã được cắt bớt do vượt quá giới hạn tối đa...]"
        return True, full_text, ""
    except Exception as e:
        return False, "", f"Lỗi đọc file PDF: {e}"


def read_image_file(file_path: str, max_chars: int = 25000) -> Tuple[bool, str, str]:
    """Read image file metadata and extract textual content via native Windows OCR."""
    try:
        from PIL import Image
        img = Image.open(file_path)
        w, h = img.size
        fmt = img.format or "IMAGE"
        mode = img.mode

        meta_info = f"Thông số tệp ảnh: Định dạng {fmt}, Kích thước {w}x{h} px, Hệ màu {mode}."

        ocr_text = ""
        try:
            import winocr
            res = winocr.recognize_pil_sync(img)
            if res and isinstance(res, dict):
                ocr_text = res.get("text", "").strip()
        except Exception:
            ocr_text = ""

        if ocr_text:
            if len(ocr_text) > max_chars:
                ocr_text = ocr_text[:max_chars] + "\n\n[...Văn bản nhận diện đã được cắt bớt do quá dài...]"
            full_text = f"{meta_info}\n\n[Nội dung văn bản nhận diện được từ hình ảnh qua OCR]:\n{ocr_text}"
        else:
            full_text = f"{meta_info}\n(Lưu ý: Không phát hiện chữ viết hoặc văn bản rõ ràng trong hình ảnh này)."

        return True, full_text, ""
    except Exception as e:
        return False, "", f"Lỗi đọc tệp ảnh: {e}"


def read_document_file(file_path: str, max_chars: int = 25000) -> Tuple[bool, str, str]:
    """
    Universal document reader for all popular formats:
    Images (PNG, JPG, JPEG, WEBP, BMP, GIF), Word, Excel, PowerPoint, PDF, Text, Code, JSON, Markdown, etc.
    Returns: (success: bool, text_content: str, error_message: str)
    """
    if not os.path.exists(file_path):
        return False, "", "Tệp không tồn tại."

    ext = os.path.splitext(file_path)[1].lower()

    IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"]

    if ext in IMAGE_EXTS:
        return read_image_file(file_path, max_chars)
    elif ext in [".docx"]:
        return read_docx_file(file_path, max_chars)
    elif ext in [".xlsx", ".xls"]:
        return read_excel_file(file_path, max_chars)
    elif ext in [".pptx"]:
        return read_pptx_file(file_path, max_chars)
    elif ext in [".pdf"]:
        return read_pdf_file(file_path, max_chars)
    else:
        # Fallback to general text & code reader (.txt, .md, .py, .json, .csv, .html, .xml, etc.)
        return read_text_file(file_path, max_chars)
