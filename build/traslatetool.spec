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

# Segundo ejecutable, identico pero con consola. Comparte el mismo Analysis,
# asi que no aumenta el tamano del bundle de forma apreciable: sirve para ver
# el traceback en vivo cuando la version silenciosa muere sin decir nada.
exe_debug = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="traslatetool-debug",
    debug=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    exe_debug,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="traslatetool",
)
