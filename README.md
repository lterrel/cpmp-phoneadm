# PhoneAdm

PhoneAdm es una aplicación de línea de comandos para administrar el inventario de anexos telefónicos de los segmentos **CPMP** y **TAZUL**.

La información local se almacena en `phoneadm_data.json`. La aplicación también puede consultar y actualizar extensiones en una PBX Yeastar mediante su API y generar un phonebook XML o un archivo Excel.

> **Importante:** la versión requerida es exactamente **Python 3.8.10**. Esta versión se mantiene por compatibilidad TLS con la PBX Yeastar utilizada por el proyecto.

## Funcionalidades

- Listar anexos por segmento y estado.
- Buscar por extensión, nombre o dirección IP.
- Mostrar anexos libres.
- Consultar información de una extensión en la PBX Yeastar.
- Crear anexos con extensión e IP disponibles.
- Editar nombre, segmento, IP y observaciones.
- Sincronizar el cambio de nombre con Yeastar usando `edit`.
- Liberar un anexo para reutilizarlo.
- Calcular capacidad de anexos e IPs disponibles.
- Generar un phonebook XML para teléfonos Yealink.
- Transferir el XML por SSH/rsync al servidor TFTP.
- Generar un listado Excel.

## Requisitos

- Linux/WSL con `asdf`.
- Python **3.8.10**.
- Acceso a la red de la PBX y, si corresponde, al servidor TFTP.
- Dependencias Python declaradas en `doc/requirements.txt`.
- Para la transferencia automática del XML: `openssh-client`, `sshpass` y `rsync`.

## Instalación

El procedimiento completo se encuentra en [`doc/instalacion.md`](doc/instalacion.md). Resumen:

```bash
git clone <URL_DEL_REPOSITORIO> phoneadm
cd phoneadm
asdf install python 3.8.10
asdf set python 3.8.10
asdf current python       # debe indicar 3.8.10
python --version          # Python 3.8.10

python -m venv venv
source venv/bin/activate
python -m pip install -r doc/requirements.txt
```

Validar que el entorno virtual utiliza la versión correcta:

```bash
command -v python        # .../phoneadm/venv/bin/python
python --version          # Python 3.8.10
python -m pip --version   # la ruta debe estar dentro de /phoneadm/venv/
python -c "import requests, urllib3, openpyxl, et_xmlfile; print('Dependencias OK')"
```

### Si se mueve el proyecto

No se debe copiar `venv` a otra ubicación. Los entornos virtuales contienen rutas absolutas. Desde la nueva ubicación:

```bash
cd /nueva/ruta/phoneadm
rm -rf venv
asdf current python
python --version          # debe ser 3.8.10
python -m venv venv
source venv/bin/activate
python -m pip install -r doc/requirements.txt
```

El código, `phoneadm_data.json`, `deny_ip.conf` y la configuración deben conservarse. Ejecutar siempre el programa desde la raíz del proyecto.

## Configuración de credenciales

Crear el archivo local de credenciales:

```bash
cp credentials.example.conf credentials.conf
chmod 600 credentials.conf
```

Completar los siguientes valores:

```ini
HOST=usuario@servidor
PASS=clave_ssh
DEST_PATH=/ruta/remota/del/phonebook/
PBX_API=https://IP_DE_LA_PBX:8088
USER_API=usuario_api
PASS_API=clave_api
```

`credentials.conf` contiene información sensible y no debe subirse al repositorio.

El token de Yeastar no se guarda en un archivo. En cada consulta o actualización, PhoneAdm realiza un `POST` contra:

```text
<PBX_API>/api/v1.1.0/login
```

con `USER_API` y `PASS_API`, y utiliza el campo `token` de la respuesta para las operaciones posteriores.

## Uso

Activar el entorno:

```bash
source venv/bin/activate
```

También se puede ejecutar directamente sin activarlo:

```bash
./venv/bin/python phoneadm.py list
```

### Comandos principales

```bash
# Listados
./phoneadm.py list
./phoneadm.py list cpmp
./phoneadm.py list tazul free

# Consultas locales y PBX
./phoneadm.py show 249
./phoneadm.py show "Nombre Apellido"
./phoneadm.py show 192.168.70.160
./phoneadm.py show free

# Capacidad
./phoneadm.py capacity phone
./phoneadm.py capacity ip
./phoneadm.py capacity ip cpmp
./phoneadm.py capacity ip tazul

# Administración
./phoneadm.py add cpmp
./phoneadm.py add tazul
./phoneadm.py edit 249
./phoneadm.py change 249
./phoneadm.py free 249

# Archivos de salida
./phoneadm.py generate
```

### `generate`

El comando es interactivo:

1. **Opción 1:** genera `result/RemotePhonebook.xml` y trata de transferirlo por SSH/rsync al servidor TFTP configurado.
2. **Opción 2:** genera un archivo Excel en `result/`.

Si la transferencia automática falla, el XML queda disponible para cargarlo manualmente.

## Rangos utilizados

- **CPMP:** extensiones disponibles entre 120 y 500; IPs `192.168.16.10` a `192.168.16.250`.
- **TAZUL:** extensiones disponibles entre 601 y 700; IPs `192.168.70.101` a `192.168.70.250`.
- Las IP incluidas en `deny_ip.conf` se excluyen del cálculo de disponibilidad.

## Estructura del proyecto

```text
phoneadm/
├── phoneadm.py                 Aplicación principal
├── phoneadm_data.json          Base de datos local de anexos
├── credentials.conf            Credenciales locales; no publicar
├── credentials.example.conf   Plantilla de credenciales
├── deny_ip.conf                IPs excluidas
├── .tool-versions              Python 3.8.10 para asdf
├── doc/
│   ├── instalacion.md          Instalación y migración
│   ├── requirements.txt        Dependencias Python fijadas
│   ├── readme.md               Notas operativas históricas
│   ├── debug.md                Diagnóstico de carga TFTP
│   ├── bugs.md                 Historial de incidencias
│   └── new_features.md         Pendientes y mejoras
├── backup/                     Copias de datos y versiones anteriores
├── result/                     XML y Excel generados
└── tools/import.py             Importador histórico de datos CSV
```

## Diagnóstico rápido

Si aparece `ModuleNotFoundError`:

```bash
source venv/bin/activate
command -v python
python --version
python -m pip --version
python -m pip install -r doc/requirements.txt
```

Si el entorno muestra Python 3.12, el `venv` fue creado con otra versión y debe recrearse.

Si falla la conexión a Yeastar con `SSLV3_ALERT_HANDSHAKE_FAILURE`, verificar primero la red y `PBX_API`. La aplicación requiere Python 3.8.10 porque la PBX utiliza una negociación TLS antigua.

Para problemas de TFTP, consultar [`doc/debug.md`](doc/debug.md).

## Respaldos y seguridad

Antes de usar `change`, `edit`, `free` o herramientas de importación, respaldar `phoneadm_data.json`:

```bash
cp phoneadm_data.json backup/phoneadm_data.json.$(date +%Y%m%d_%H%M%S).bak
```

No publicar `credentials.conf`, contraseñas ni tokens. El script `api_example_usage.sh` es una referencia para llamadas a la API y debe revisarse antes de utilizarse, especialmente si contiene credenciales de un entorno real.
