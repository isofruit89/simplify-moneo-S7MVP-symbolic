"""Service layer between the user interface and the conversion core.

The JSON output is produced exclusively by ``core.convert_tia_xml_to_moneo_json``
(into a temporary file) and copied byte for byte to the target on save.
The analysis of skipped variables is informational only and does not affect
the output.
"""
import json
import os
import tempfile
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import core

NS_MEMBER = "{http://www.siemens.com/automation/Openness/SW/Interface/v5}Member"
NAMESPACE = {"ns": "http://www.siemens.com/automation/Openness/SW/Interface/v5"}


@dataclass
class Conversion:
    id: str
    xml_path: str
    db_name: str
    json_bytes: bytes
    signals: list
    skipped: list = field(default_factory=list)

    @property
    def default_filename(self) -> str:
        return Path(self.xml_path).stem + ".json"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ok": True,
            "xmlPath": self.xml_path,
            "fileName": Path(self.xml_path).name,
            "dbName": self.db_name,
            "defaultFilename": self.default_filename,
            "signals": self.signals,
            "skipped": self.skipped,
        }


def _clean_type(datatype: str) -> str:
    # Same cleanup as in core.parse_members (diagnostics only).
    return datatype.split()[0].split("[")[0].split("of")[-1].strip().upper().replace('"', "")


def _collect_skipped(members, parent_path, out):
    """Mirrors core.parse_members and collects what it discards."""
    for member in members:
        name = member.attrib.get("Name")
        datatype = member.attrib.get("Datatype")
        if not name or not datatype:
            out.append({
                "path": f"{parent_path}.{name}" if parent_path and name else (name or parent_path or "?"),
                "datatype": datatype or "",
                "reason": "Name or data type missing",
            })
            continue
        clean = _clean_type(datatype)
        full_path = f"{parent_path}.{name}" if parent_path else name
        nested = member.findall("./" + NS_MEMBER)
        if nested:
            _collect_skipped(nested, full_path, out)
            continue
        if not core.s7_to_moneo.get(clean):
            if clean == "ARRAY":
                reason = "Arrays are not transferred"
            elif clean == "STRUCT":
                reason = "Struct without elements"
            elif datatype.strip().startswith('"'):
                reason = "UDT/PLC data type without resolved elements"
            else:
                reason = f"Data type {clean} is not supported"
            out.append({"path": full_path, "datatype": datatype, "reason": reason})


def analyze(xml_path: str) -> Conversion:
    """Converts the XML with the original core and returns result + diagnostics."""
    xml_path = str(Path(xml_path).resolve())
    fd, tmp = tempfile.mkstemp(suffix=".json", prefix="tia2moneo_")
    os.close(fd)
    try:
        core.convert_tia_xml_to_moneo_json(xml_path, tmp)
        json_bytes = Path(tmp).read_bytes()
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass

    signals = json.loads(json_bytes.decode("utf-8"))

    root = ET.parse(xml_path).getroot()
    db_elem = root.find(".//Name")
    db_name = db_elem.text if db_elem is not None else "UnknownDB"
    skipped: list = []
    _collect_skipped(root.findall(".//ns:Section[@Name='Static']/ns:Member", NAMESPACE), "", skipped)

    return Conversion(
        id=uuid.uuid4().hex,
        xml_path=xml_path,
        db_name=db_name or "UnknownDB",
        json_bytes=json_bytes,
        signals=signals,
        skipped=skipped,
    )


def save(conversion: Conversion, target: str) -> str:
    """Writes the bytes produced by the core unchanged to the target."""
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(conversion.json_bytes)
    return str(target_path)


def describe_error(exc: Exception) -> str:
    if isinstance(exc, ET.ParseError):
        return f"The file is not valid XML ({exc})."
    if isinstance(exc, FileNotFoundError):
        return "The file was not found."
    if isinstance(exc, PermissionError):
        return "Access to the file denied (it may be open in another program or read-only)."
    return f"{type(exc).__name__}: {exc}"

