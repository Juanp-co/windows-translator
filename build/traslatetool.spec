# PyInstaller spec — se ejecuta EN Windows (local o en el runner de CI).
#   pyinstaller build/traslatetool.spec
#
# --onedir (no --onefile): arranque instantáneo. --onefile descomprimiría
# ~300 MB en %TEMP% en cada arranque, varios segundos de espera.

from pathlib import Path

ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / "app" / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(ROOT / "models"), "models")],
    hiddenimports=[
        "pystray._win32",
        "PIL._tkinter_finder",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # Nada de esto se usa; fuera del bundle.
        "torch", "stanza", "numpy.distutils", "matplotlib",
        "scipy", "pandas", "pytest", "setuptools",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="traslatetool",
    debug=False,
    strip=False,
    upx=False,
    console=False,          # sin ventana de consola: app de bandeja
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="traslatetool",
)
