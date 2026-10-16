# Procedimiento de instalación y migración

## Requisito obligatorio

La aplicación debe ejecutarse con **Python 3.8.10**. La versión está fijada en `.tool-versions`:

```text
python 3.8.10
```

El entorno virtual (`venv`) no debe copiarse entre directorios ni entre equipos. Contiene rutas absolutas y debe recrearse cuando se clona o mueve el proyecto.

## Instalación desde un repositorio Git

```bash
git clone <URL_DEL_REPOSITORIO> phoneadm
cd phoneadm

# Instala Python si todavía no existe en asdf
asdf install
asdf current python
python --version       # debe mostrar Python 3.8.10

python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r doc/requirements.txt
```

Validar el entorno:

```bash
command -v python       # debe terminar en /phoneadm/venv/bin/python
python --version        # Python 3.8.10
python -m pip --version # debe mencionar /phoneadm/venv/
python -c "import requests, urllib3, openpyxl, et_xmlfile; print('Dependencias OK')"
```

## Migración a otro directorio

Si se mueve el proyecto, se conserva el código, `phoneadm_data.json`, `credentials.conf` y los archivos de configuración, pero se elimina y recrea únicamente el entorno virtual:

```bash
cd /nueva/ruta/phoneadm
rm -rf venv
asdf current python
python --version       # debe mostrar Python 3.8.10
python -m venv venv
source venv/bin/activate
python -m pip install -r doc/requirements.txt
```

También es posible ejecutar sin activar el entorno:

```bash
./venv/bin/python phoneadm.py show 249
```

Siempre debe ejecutarse desde la raíz del proyecto, porque `credentials.conf`, `result/` y algunos archivos de operación se resuelven usando el directorio actual.

## Configuración

Crear `credentials.conf` a partir de `credentials.example.conf` y completar los datos reales:

```bash
cp credentials.example.conf credentials.conf
chmod 600 credentials.conf
```

El archivo contiene dos grupos de datos:

- `HOST`, `PASS`, `DEST_PATH`: conexión SSH/TFTP usada por `generate` opción 1.
- `PBX_API`, `USER_API`, `PASS_API`: acceso a la API Yeastar.

El token de Yeastar no se almacena. La aplicación lo solicita en cada operación que consulta o actualiza la PBX mediante `/api/v1.1.0/login`.

No se deben subir credenciales reales al repositorio.

## Dependencias del sistema

Las operaciones locales solo requieren Python y las dependencias de `doc/requirements.txt`. Para generar y transferir el phonebook XML se requieren además:

```bash
sudo apt install openssh-client sshpass rsync
```

`curl`, `jq` y `zsh` son necesarios únicamente para utilizar `api_example_usage.sh`.

## Comprobación funcional

```bash
./phoneadm.py list
./phoneadm.py show 249
```

Si `show` muestra los datos locales pero falla al consultar Yeastar, revisar conectividad hacia `PBX_API`, usuario/contraseña y compatibilidad TLS de la PBX.
