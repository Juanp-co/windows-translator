# traslatetool — contexto del proyecto

Traductor global ES↔EN para Windows. Segundo plano, icono en bandeja,
traducción **100% offline** (sin API, sin cuenta, sin límite).

## Estado actual

| | |
|---|---|
| Build en CI | Verde. Produce `.exe` firmado + instalador |
| Instalación en Windows | Funciona |
| **Atajos** | **NO funcionan — es el problema abierto** |
| Traducción (motor) | Verificada en macOS y en el runner Windows |

**Síntoma exacto:** el usuario instaló, pulsó `Ctrl+Alt+R` sobre texto en el
Bloc de notas y no ocurrió absolutamente nada. Ni popup, ni error.

## Modo de uso pedido por el usuario

- **Popup EN→ES: automático**, sin pulsar nada. Al soltar el ratón tras
  arrastrar sobre texto en inglés, sale el popup. Implementado en
  `app/watcher.py` (listener de ratón: pulsar → arrastrar → soltar → Ctrl+C).
  `Ctrl+Alt+R` se mantiene como respaldo manual.
- **Reemplazo ES→EN: `Ctrl+W`.** Pedido explícitamente por el usuario.
  ⚠️ `Ctrl+W` ya significa "cerrar pestaña" en navegadores y editores, y
  pynput **no suprime** la pulsación, así que también cerrará la pestaña.
  Si resulta inviable en la práctica, `<ctrl>+<alt>+w` es el sustituto
  directo — una línea en `app/config.py`.

## Por qué existe este fichero

El desarrollo se hizo **desde un Mac**, donde es imposible ejecutar el código:
los atajos, el portapapeles y el popup son específicos de Windows. Todo se
validó estáticamente. Eso ya causó tres fallos que solo aparecieron en Windows:

1. `%errLevel%` en vez de `%errorlevel%` → el `.bat` moría sin mostrar nada
2. `UnicodeEncodeError` → la consola del runner es cp1252 y el script imprimía `↓ ✓`
3. `if: ${{ secrets.X }}` en un paso → contexto no permitido, GitHub rechazaba el workflow

**Si estás leyendo esto en Windows: puedes ejecutar el código. Úsalo.**
No repitas el patrón de validar leyendo.

## Arranque rápido en Windows

```powershell
git clone https://github.com/Juanp-co/windows-translator
cd windows-translator
py -3.11 -m venv .venv            # 3.11: wheels estables de ctranslate2
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\fetch_models.py    # ~190 MB
python -m app.main                # ejecuta desde fuente, con consola
```

Ejecutar desde fuente es el ciclo rápido: segundos, no los 6 minutos del CI.

## Dónde mirar cuando algo falla

```
%LOCALAPPDATA%\traslatetool\traslatetool.log
```

`app/log.py` registra arranque, registro de atajos, cada disparo, cada
traducción y todos los tracebacks. La app se compila con `console=False`,
así que **sin el log una excepción al arrancar la mata en silencio**.
También hay un `traslatetool-debug.exe` con consola en el bundle.

## Arquitectura

```
app/
  config.py      atajos, rutas, tiempos del portapapeles
  translator.py  ctranslate2 + sentencepiece, carga perezosa
  selection.py   Ctrl+C sintetico -> leer portapapeles -> restaurar
  popup.py       tkinter; cola + root.after (los atajos llegan en otros hilos)
  main.py        pystray (bandeja) + pynput (atajos)
  log.py         log a fichero
scripts/fetch_models.py   descarga modelos Argos
build/traslatetool.spec   PyInstaller
installer/                INSTALAR.bat + instalar.ps1 (descargan e instalan)
.github/workflows/        build en runner Windows + firma + release
```

**No se usa `argostranslate`**: arrastra `stanza`, que arrastra PyTorch
(~2 GB de bundle). Se usan directamente `ctranslate2` + `sentencepiece`,
que es lo que Argos tiene por debajo. El corte en frases lo hace un regex
en `translator.py`, sustituyendo a `stanza`.

## Decisiones que ya costaron tiempo — no rehacerlas

**Modelos Argos fijados a v1.0 en ambas direcciones.** El paquete `es_en-1_9`
usa BPE de subword-nmt en vez de SentencePiece (su `bpe.model` es texto plano,
no un ModelProto) y pesa 285 MB por el `stanza/ancora.pt`. La v1.0 usa
SentencePiece y pesa 87 MB. `fetch_models.py` valida el formato y falla si
alguien sube la versión.

**`argos-net.com` devuelve 403 sin User-Agent de navegador.**

**Windows: consola cp1252.** No imprimir caracteres fuera de ese juego.
El workflow fuerza `PYTHONUTF8=1`.

**`suppress` de pynput es del listener entero, no por atajo.** Verificado en
el fuente: `GlobalHotKeys.__init__` pasa `**kwargs` a `Listener` y no activa
supresión. Es decir: **un atajo dispara nuestra acción Y llega igual a la app
en primer plano.** Crítico al elegir combinaciones que ya significan algo.

**PyInstaller `--onedir`, no `--onefile`.** Con ~300 MB, onefile descomprime
en `%TEMP%` en cada arranque.

## Medido (macOS, Intel)

| | |
|---|---|
| Modelos en disco | 191 MB |
| RAM en reposo (sin cargar modelos) | 10 MB |
| RAM con una dirección | 174 MB |
| RAM con las dos | 283 MB |
| Primera traducción | ~2 s |
| Siguientes | ~0,14 s |

## Hipótesis para el fallo de los atajos

Sin verificar — hay que comprobarlas ejecutando:

1. **La app no está corriendo.** Mirar `traslatetool.exe` en el Administrador
   de tareas y si aparece el icono azul en la bandeja.
2. **`tk.Tk()` falla en el bundle** (tcl/tk no empaquetado) → `popup.start_loop()`
   revienta en el hilo principal y mata el proceso en silencio.
3. **`pystray.Icon.run()` en un hilo secundario.** En Windows puede necesitar
   el hilo principal para su bomba de mensajes.
4. **El listener de pynput no llega a registrarse.** El log lo dirá:
   busca `listener de atajos ACTIVO`.
5. **Conflicto de combinación** con otra app ya instalada.

El log distingue entre todas ellas. Empezar por ahí.

## Firma

Certificado **autofirmado** en `signing/` (la clave privada y el `.pfx` están
gitignored; en el repo solo va `cert.cer`, público). Da identidad al binario
pero **no elimina SmartScreen en un PC cualquiera** — sí en el propio, tras
importar `cert.cer`. Los secretos del repo son `SIGNING_PFX_BASE64` y
`SIGNING_PFX_PASSWORD` (contraseña: `traslatetool`), como **repository
secrets**, no environment.

## Entrega

Release con URL fija, descargable sin token:

```
https://github.com/Juanp-co/windows-translator/releases/latest/download/traslatetool-setup.exe
```

Los artefactos de Actions dan 401 sin autenticar aunque el repo sea público;
los assets de una release, no. Por eso existe el paso de release.
