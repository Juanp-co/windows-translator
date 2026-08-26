# traslatetool - descarga e instalacion desatendida
# Sin acentos a proposito: la consola de Windows usa cp850/cp1252 y los
# mezclaria. Ejecutar via INSTALAR.bat, que se encarga de elevar permisos.

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'   # Invoke-WebRequest va ~10x mas rapido sin barra

$Base    = 'https://github.com/Juanp-co/windows-translator/releases/latest/download'
$ExeUrl  = "$Base/traslatetool-setup.exe"
$CertUrl = "$Base/cert.cer"
$Work    = Join-Path $env:TEMP "traslatetool-install"

function Say($msg, $color = 'Gray') { Write-Host $msg -ForegroundColor $color }

Say ""
Say "  traslatetool - instalador" Cyan
Say "  =========================" Cyan
Say ""

# --- 1. Comprobar permisos --------------------------------------------------
$admin = ([Security.Principal.WindowsPrincipal] `
          [Security.Principal.WindowsIdentity]::GetCurrent()
         ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $admin) {
    Say "  ERROR: hacen falta permisos de administrador." Red
    Say "  Cierra esto y haz clic derecho en INSTALAR.bat -> Ejecutar como administrador." Yellow
    Read-Host "`n  Pulsa Enter para salir"
    exit 1
}

# TLS 1.2: Windows 10 antiguo negocia TLS 1.0 por defecto y GitHub lo rechaza.
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

New-Item -ItemType Directory -Force -Path $Work | Out-Null

try {
    # --- 2. Descargar -------------------------------------------------------
    Say "  [1/4] Descargando certificado..."
    Invoke-WebRequest -Uri $CertUrl -OutFile "$Work\cert.cer" -UseBasicParsing

    Say "  [2/4] Descargando instalador (unos 200 MB, puede tardar)..."
    $t0 = Get-Date
    Invoke-WebRequest -Uri $ExeUrl -OutFile "$Work\setup.exe" -UseBasicParsing
    $secs = [int]((Get-Date) - $t0).TotalSeconds
    $mb   = [math]::Round((Get-Item "$Work\setup.exe").Length / 1MB, 1)
    Say "        $mb MB en $secs s" DarkGray

    # --- 3. Validar lo descargado ------------------------------------------
    # Una descarga cortada o una pagina de error HTML pasarian desapercibidas
    # y el instalador fallaria con un mensaje inutil. Se comprueba antes.
    $file = Get-Item "$Work\setup.exe"
    if ($file.Length -lt 50MB) {
        throw "El instalador descargado pesa solo $mb MB. Descarga incompleta."
    }
    $head = [char[]](Get-Content "$Work\setup.exe" -Encoding Byte -TotalCount 2) -join ''
    if ($head -ne 'MZ') {
        throw "El archivo descargado no es un ejecutable de Windows."
    }
    $sha = (Get-FileHash "$Work\setup.exe" -Algorithm SHA256).Hash.ToLower()
    Say "        sha256: $sha" DarkGray

    # --- 4. Confiar en el certificado --------------------------------------
    # El certificado es autofirmado: sin importarlo, SmartScreen avisa.
    # TrustedPublisher evita el aviso; Root hace que la firma valide.
    Say "  [3/4] Importando certificado..."
    Import-Certificate -FilePath "$Work\cert.cer" `
        -CertStoreLocation Cert:\LocalMachine\TrustedPublisher | Out-Null
    Import-Certificate -FilePath "$Work\cert.cer" `
        -CertStoreLocation Cert:\LocalMachine\Root | Out-Null

    $sig = Get-AuthenticodeSignature "$Work\setup.exe"
    Say "        firma: $($sig.Status)" DarkGray

    # --- 5. Instalar --------------------------------------------------------
    # /SILENT: barra de progreso sin asistente. /VERYSILENT no muestra nada.
    Say "  [4/4] Instalando..."
    $p = Start-Process -FilePath "$Work\setup.exe" `
                       -ArgumentList '/SILENT','/NORESTART' `
                       -Wait -PassThru
    if ($p.ExitCode -ne 0) { throw "El instalador termino con codigo $($p.ExitCode)." }

    Say ""
    Say "  LISTO" Green
    Say ""
    Say "  Busca el icono azul en la bandeja del sistema (abajo a la derecha)."
    Say "  Arranca solo cada vez que inicies sesion."
    Say ""
    Say "  ATAJOS" Cyan
    Say "    Ctrl+Alt+R   selecciona texto -> popup con la traduccion"
    Say "    Ctrl+Alt+Y   selecciona texto -> lo reemplaza por la traduccion"
    Say ""
    Say "  Detecta el idioma solo: sirve en ambos sentidos." DarkGray
    Say "  La primera traduccion tarda ~2s (carga el modelo); el resto ~0.15s." DarkGray
    Say "  Funciona sin internet." DarkGray
}
catch {
    Say ""
    Say "  FALLO: $($_.Exception.Message)" Red
    Say ""
    Say "  Alternativa manual:" Yellow
    Say "    https://github.com/Juanp-co/windows-translator/releases/latest"
}
finally {
    Remove-Item $Work -Recurse -Force -ErrorAction SilentlyContinue
}

Read-Host "`n  Pulsa Enter para cerrar"
