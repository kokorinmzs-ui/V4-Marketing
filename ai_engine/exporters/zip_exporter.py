"""ZIP Exporter — creates client-package.zip from package files."""

import zipfile
import io
from typing import Any


class ZipExporter:
    """Exports package files as a ZIP archive."""

    REQUIRED_FILES = [
        "01-README.txt",
        "02-EXECUTION-DASHBOARD.html",
        "03-CONTENT-LIBRARY.html",
        "04-SALES-SCRIPTS.html",
        "05-KPI-GUIDE.html",
        "06-PROJECT-METADATA.json",
    ]

    def export(self, files: dict[str, str]) -> bytes:
        """Create a ZIP archive from file content dict.

        Args:
            files: dict of filename -> content string

        Returns:
            ZIP file as bytes

        Raises:
            ValueError if required files missing or empty files found
        """
        for req in self.REQUIRED_FILES:
            if req not in files:
                raise ValueError(f"Missing required file: {req}")
            if not files[req] or not files[req].strip():
                raise ValueError(f"Empty file: {req}")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, content in files.items():
                zf.writestr(filename, content)
        return buf.getvalue()

    def export_to_file(self, files: dict[str, str], path: str) -> int:
        """Export ZIP to a file path. Returns file size in bytes."""
        data = self.export(files)
        with open(path, "wb") as f:
            f.write(data)
        return len(data)

    @staticmethod
    def validate_zip(zip_data: bytes) -> dict[str, Any]:
        """Validate a ZIP archive.

        Returns dict with validation results.
        """
        result: dict[str, Any] = {"valid": False, "size_bytes": len(zip_data), "files": [], "errors": []}
        try:
            buf = io.BytesIO(zip_data)
            with zipfile.ZipFile(buf, "r") as zf:
                names = zf.namelist()
                result["files"] = names
                for req in ZipExporter.REQUIRED_FILES:
                    if req not in names:
                        result["errors"].append(f"Missing: {req}")
                for name in names:
                    info = zf.getinfo(name)
                    if info.file_size == 0:
                        result["errors"].append(f"Empty: {name}")
                result["valid"] = len(result["errors"]) == 0
        except Exception as e:
            result["errors"].append(f"ZIP error: {e}")
        return result