"""Conversion core: TIA Portal XML -> moneo JSON.

The functions ``parse_members`` and ``convert_tia_xml_to_moneo_json`` and the
table ``s7_to_moneo`` are taken 1:1 from the original ``TIAExportv2.py``
(TIAExportv2.exe, 2025-09-16). The bytecode is identical, see
``tests/test_regression.py``. This includes the original console message in
``convert_tia_xml_to_moneo_json``, which is therefore kept unchanged.

DO NOT MODIFY THIS FILE - the output must match the previous exe exactly.
"""
import xml.etree.ElementTree as ET
import json

s7_to_moneo = {
    "INT": "INT32", "SINT": "INT32", "DINT": "INT32",
    "USINT": "UINT32", "UINT": "UINT32", "UDINT": "UINT32",
    "LINT": "INT64", "ULINT": "UINT64",
    "REAL": "FLOAT", "LREAL": "DOUBLE",
    "CHAR": "STRING", "WCHAR": "STRING", "STRING": "STRING", "WSTRING": "STRING",
    "BOOL": "BOOLEAN",
    "BYTE": "UINT32", "WORD": "UINT32", "DWORD": "UINT32", "LWORD": "UINT64",
}


def parse_members(members, parent_path, db_name):
    moneo_data = []
    for member in members:
        name = member.attrib.get("Name")
        datatype = member.attrib.get("Datatype")
        if not name or not datatype:
            continue

        clean_type = datatype.split()[0].split("[")[0].split("of")[-1].strip().upper().replace('"', "")
        full_path = f"{parent_path}.{name}" if parent_path else name

        nested_members = member.findall("./{http://www.siemens.com/automation/Openness/SW/Interface/v5}Member")
        if nested_members:
            moneo_data.extend(parse_members(nested_members, full_path, db_name))
            continue

        moneo_type = s7_to_moneo.get(clean_type)
        if not moneo_type:
            continue
        moneo_data.append({"Address": f"PLC.Blocks.{db_name}.{full_path};{clean_type}", "MeasurementName": name, "Unit": "K", "Type": moneo_type})
    return moneo_data


def convert_tia_xml_to_moneo_json(xml_file, json_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    namespace = {"ns": "http://www.siemens.com/automation/Openness/SW/Interface/v5"}
    db_name_elem = root.find(".//Name")
    db_name = db_name_elem.text if db_name_elem is not None else "UnknownDB"

    top_members = root.findall(".//ns:Section[@Name='Static']/ns:Member", namespace)
    moneo_data = parse_members(top_members, "", db_name)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(moneo_data, f, separators=(",", ":"), ensure_ascii=False)

    print(f"Konvertierung abgeschlossen! Ergebnis: {json_file}")
