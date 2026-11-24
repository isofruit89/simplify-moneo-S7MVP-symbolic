# PyInstaller spec: python -m PyInstaller TIA2moneo.spec
a = Analysis(
    ["app.py"],
    datas=[
        ("ui/index.html", "ui"),
        ("ui/style.css", "ui"),
        ("ui/app.js", "ui"),
    ],
    excludes=["tkinter"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="TIA2moneo",
    console=False,
    upx=False,
)
