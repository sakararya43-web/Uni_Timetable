import csv
import io
import re

from app.middleware.error_handler import DomainException

FORMULA_PREFIXES = ("=", "+", "-", "@")


def sanitize_formula_injection(val: str) -> str:
    """Neutralize spreadsheet formula injection on any cell value (PRD §23, Task P4.2)."""
    if not val:
        return val
    cleaned = val.strip()
    if cleaned.startswith(FORMULA_PREFIXES):
        return f"'{cleaned}"
    return cleaned


def decode_csv_bytes(raw_bytes: bytes, max_size_bytes: int) -> str:
    """
    Validate file size, sniff non-binary contents, and decode UTF-8 with BOM handling.
    Rejects binary or undecodable files with clear error codes.
    """
    if len(raw_bytes) > max_size_bytes:
        max_mb = max_size_bytes // (1024 * 1024)
        raise DomainException(
            code="FILE_TOO_LARGE",
            message=f"Uploaded file exceeds the maximum allowed size of {max_mb} MB.",
            status_code=413,
        )

    # Sniff binary content: CSV text must not contain null bytes
    if b"\x00" in raw_bytes[:1024]:
        raise DomainException(
            code="INVALID_FILE_TYPE",
            message="Uploaded file contains binary content. Please upload a plain text CSV file.",
            status_code=422,
        )

    # Handle UTF-8 with BOM (utf-8-sig) or standard UTF-8
    try:
        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            return raw_bytes.decode("utf-8-sig")
        return raw_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        raise DomainException(
            code="INVALID_ENCODING",
            message=f"The uploaded file is not a valid UTF-8 text file. Decoding failed at byte {e.start}.",
            status_code=422,
        ) from e


def parse_csv_text(content: str, max_rows: int) -> tuple[list[str], list[dict[str, str]]]:
    """
    Parse CSV text with header normalization (trimmed, lowercased).
    Returns normalized headers and a list of row dicts containing 1-based line numbers.
    """
    if not content.strip():
        raise DomainException(
            code="EMPTY_FILE",
            message="The uploaded CSV file is empty.",
            status_code=422,
        )

    f = io.StringIO(content.strip(), newline=None)
    reader = csv.reader(f)

    try:
        raw_headers = next(reader)
    except StopIteration as e:
        raise DomainException(
            code="EMPTY_FILE",
            message="The uploaded CSV file has no content or headers.",
            status_code=422,
        ) from e

    # Normalize headers: strip quotes, trim, lowercase
    headers = [re.sub(r"^\ufeff", "", h).strip().lower() for h in raw_headers]
    if not headers or all(h == "" for h in headers):
        raise DomainException(
            code="INVALID_HEADERS",
            message="No valid headers found in the first row of the CSV file.",
            status_code=422,
        )

    rows: list[dict[str, str]] = []
    line_number = 1  # Header is line 1

    for row_values in reader:
        line_number += 1
        if not row_values or all(c.strip() == "" for c in row_values):
            continue  # Skip blank lines

        if len(rows) >= max_rows:
            raise DomainException(
                code="ROW_LIMIT_EXCEEDED",
                message=f"CSV file exceeds the maximum allowed row limit of {max_rows} rows.",
                status_code=422,
            )

        row_dict: dict[str, str] = {"_row_num": str(line_number)}
        for idx, h in enumerate(headers):
            val = row_values[idx].strip() if idx < len(row_values) else ""
            row_dict[h] = val

        rows.append(row_dict)

    if not rows:
        raise DomainException(
            code="NO_DATA_ROWS",
            message="CSV file contains headers but no valid data rows.",
            status_code=422,
        )

    return headers, rows
