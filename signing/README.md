# Firma autofirmada

`traslatetool.pfx` — certificado + clave privada. Contraseña: `traslatetool`.
`cert.cer` — solo la parte pública. Es la que se instala en el Windows destino.
`cert.pem` / `key.pem` — fuentes con las que se generó el .pfx.

## Qué consigue y qué NO consigue

| | Autofirmado | Certificado de CA (200-400 €/año) |
|---|---|---|
| El .exe lleva identidad y no se puede alterar | Sí | Sí |
| Sin aviso en TU PC (tras importar cert.cer) | **Sí** | Sí |
| Sin aviso en un PC cualquiera | **No** | Sí (con reputación) |

Para uso personal es suficiente: importas `cert.cer` una vez en tu Windows y
SmartScreen deja de avisar en esa máquina.

## Cargar el certificado en GitHub Actions

```bash
base64 -i traslatetool.pfx | pbcopy
```

En el repo → Settings → Secrets and variables → Actions → New secret:

- `SIGNING_PFX_BASE64` → pega lo copiado
- `SIGNING_PFX_PASSWORD` → `traslatetool`

## Confiar en el certificado en el Windows destino

Una sola vez, PowerShell **como administrador**:

```powershell
Import-Certificate -FilePath .\cert.cer -CertStoreLocation Cert:\LocalMachine\TrustedPublisher
Import-Certificate -FilePath .\cert.cer -CertStoreLocation Cert:\LocalMachine\Root
```

A partir de ahí el instalador y el .exe se abren sin aviso.

## Regenerar (caduca en 2036)

```bash
openssl req -x509 -newkey rsa:3072 -keyout key.pem -out cert.pem -days 3650 -nodes \
  -subj "/CN=traslatetool/O=traslatetool/C=ES" \
  -addext "keyUsage=digitalSignature" \
  -addext "extendedKeyUsage=codeSigning" \
  -addext "basicConstraints=critical,CA:FALSE"
openssl pkcs12 -export -out traslatetool.pfx -inkey key.pem -in cert.pem \
  -passout pass:traslatetool -name "traslatetool"
openssl x509 -in cert.pem -outform DER -out cert.cer
```
