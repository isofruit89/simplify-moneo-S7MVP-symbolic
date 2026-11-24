"""Regression test: the new version must produce exactly the same JSON as the old exe.

Run (Python 3.12, from the tia2moneo folder):
    python tests/test_regression.py [more.xml ...]

Additional real TIA exports can be passed as arguments or placed in
tests/fixtures.
"""
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import core  # noqa: E402
import original  # noqa: E402
import service  # noqa: E402


def check_bytecode(orig):
    for fn in ("parse_members", "convert_tia_xml_to_moneo_json"):
        a, b = orig[fn].__code__, getattr(core, fn).__code__
        assert a.co_code == b.co_code, f"{fn}: bytecode differs"
        assert a.co_consts == b.co_consts, f"{fn}: constants differ"
        assert a.co_names == b.co_names, f"{fn}: names differ"
    assert list(orig["s7_to_moneo"].items()) == list(core.s7_to_moneo.items()), "type table differs"
    print("OK  bytecode of parse_members / convert_tia_xml_to_moneo_json / s7_to_moneo identical")


def run(func, xml):
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "out.json"
        try:
            func(str(xml), str(out))
        except Exception as exc:
            return ("error", type(exc).__name__)
        return ("ok", out.read_bytes())


def via_service(xml, out):
    service.save(service.analyze(xml), out)


def check_file(orig, xml):
    expected = run(orig["convert_tia_xml_to_moneo_json"], xml)
    for label, func in (("core", core.convert_tia_xml_to_moneo_json), ("GUI path", via_service)):
        got = run(func, xml)
        assert got == expected, f"{xml.name}: {label} differs from original\n  expected: {expected!r}\n  got:      {got!r}"
    status = f"{len(expected[1])} bytes" if expected[0] == "ok" else f"error {expected[1]} (same as original)"
    print(f"OK  {xml.name}: identical ({status})")


def main(extra):
    orig = original.load_module()
    check_bytecode(orig)
    files = sorted((HERE / "fixtures").glob("*.xml")) + [Path(p) for p in extra]
    for xml in files:
        check_file(orig, xml)
    print(f"\nAll {len(files)} files byte-identical to the original.")


def test_regression():
    main([])


if __name__ == "__main__":
    main(sys.argv[1:])
