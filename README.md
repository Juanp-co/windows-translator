# traslatetool

Traductor global ES↔EN para Windows. Corre en segundo plano, sin ventana, con icono
en la bandeja del sistema. Traducción **100% offline** con modelos Argos sobre
CTranslate2 — sin API, sin cuenta, sin límite de caracteres.

## Atajos

| Atajo | Selección | Acción |
|---|---|---|
| `Ctrl+Alt+R` | Texto en inglés | Popup con la traducción al español |
| `Ctrl+Alt+Y` | Texto en español | Borra la selección y escribe el inglés en su lugar |

Ambos detectan el idioma solos y traducen en la dirección contraria, así que
funcionan aunque te equivoques de atajo. Se cambian en `app/config.py`.

## Medido en macOS (Intel, Python 3.13)

| | |
|---|---|
| Modelos en disco | **191 MB** (2 × 90 MB + vocabularios) |
| RAM en reposo, modelos sin cargar | **10 MB** |
| RAM con una dirección cargada | **174 MB** |
| RAM con las dos direcciones | **283 MB** |
| Primera traducción (incluye cargar el modelo) | ~2 s |
| Traducciones siguientes | **~0,14 s** |

Ejemplos reales de salida:

```
Hola, necesito revisar el informe antes de la reunión de mañana.
 → Hey, I need to check the report before the meeting tomorrow.

The deployment failed because the database migration timed out.
 → El despliegue falló porque la migración de la base de datos se agotó.
```

## Arquitectura

```
  Ctrl+Alt+R / Ctrl+Alt+E
          │
          ▼
  pynput  ──► envía Ctrl+C, lee el portapapeles
          │
          ▼
  translator.py ──► sentencepiece (tokeniza)
                    ctranslate2   (traduce, int8)
                    sentencepiece (destokeniza)
          │
          ├──► popup.py   (tkinter, siempre encima)   [modo R]
          └──► escribe en portapapeles + Ctrl+V       [modo E]
```

Sin servidor, sin HTTP, sin `argostranslate` (que arrastraría PyTorch vía `stanza`).
Solo `ctranslate2` + `sentencepiece`, que es lo que Argos usa por debajo.

## Estructura

```
traslatetool/
├── app/
│   ├── config.py       Atajos, rutas, parámetros del modelo
│   ├── translator.py   Carga perezosa de modelos + traducción
│   ├── selection.py    Copiar la selección / pegar el reemplazo
│   ├── popup.py        Ventana tkinter del resultado
│   └── main.py         Bandeja del sistema + registro de atajos
├── scripts/
│   └── fetch_models.py Descarga y extrae los modelos Argos a models/
├── build/
│   └── traslatetool.spec   Receta de PyInstaller
├── .github/workflows/
│   └── build-windows.yml   CI que compila el .exe en Windows
└── models/             (generado, no versionado)
    ├── en_es/  model.bin, shared_vocabulary.txt, sentencepiece.model
    └── es_en/  ...
```

## Desarrollo en macOS

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_models.py
python -c "from app.translator import translate; print(translate('hola qué tal','es','en'))"
```

En Mac puedes probar y afinar **translator.py** entero. Los atajos globales, el
portapapeles y el popup solo se prueban de verdad en Windows.

## Generar el .exe

**Docker no sirve para esto.** Los contenedores Windows comparten el kernel del
host, así que necesitan un host Windows; Docker Desktop en macOS levanta una VM
Linux y no puede ejecutarlos. Y PyInstaller no compila cruzado: el bundle lleva
binarios nativos de Windows.

La solución es el workflow de GitHub Actions incluido — un runner Windows real:

```bash
cd ~/Desktop/traslatetool
git init && git add -A && git commit -m "traslatetool"
gh repo create traslatetool --private --source=. --push
# Actions → Build Windows → descargar traslatetool-setup.exe
```

Antes del primer push, carga el certificado de firma en los secretos del repo:
ver `signing/README.md`.

Alternativa sin CI: una VM de Windows en el Mac (es Intel, virtualiza x86
nativo) y `pyinstaller build/traslatetool.spec`.

## Firma

El `.exe` va firmado con un certificado autofirmado (`signing/`). Eso le da
identidad y detecta manipulación, pero **no elimina el aviso de SmartScreen en
un PC cualquiera** — para eso hace falta un certificado de CA de pago. En tu
propio Windows sí desaparece, importando `cert.cer` una vez. Instrucciones en
`signing/README.md`.
