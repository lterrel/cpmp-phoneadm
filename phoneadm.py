#!/usr/bin/env python3
import json
import os
import re
import sys
import unicodedata
from datetime import datetime

import requests  # Necesario para llamadas HTTP a la API Yeastar
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_FILE = os.path.join(os.path.dirname(__file__), "phoneadm_data.json")


class PhoneRegistry:
    def __init__(
        self,
        id,
        extension,
        name,
        last_name,
        createAt,
        updateAt,
        ip,
        category,
        status,
        obs="",
    ):
        self.id = id
        self.extension = extension
        self.name = name
        self.last_name = last_name
        self.createAt = createAt
        self.updateAt = updateAt
        self.ip = ip
        self.category = category  # 'cpmp' o 'tazul'
        self.status = status  # 'active' o 'free'
        self.obs = obs

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(d):
        return PhoneRegistry(
            d["id"],
            d["extension"],
            d["name"],
            d["last_name"],
            d["createAt"],
            d["updateAt"],
            d["ip"],
            d["category"],
            d["status"],
            d.get("obs", ""),
        )


class PhoneBook:
    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file
        self.registries = self.load()

    def change(self, value):
        import re
        from datetime import datetime

        # Buscar registro
        record = None
        for r in self.registries:
            if str(r.extension) == str(value) or r.name.lower() == value.lower():
                record = r
                break
        if not record:
            print("No match found. No existe un anexo con ese número o nombre.")
            return

        print("Información actual del anexo:")
        print(f"  name: {record.name}")
        print(f"  category: {record.category}")
        print(f"  ip: {record.ip}")
        print(f"  obs: {record.obs}")

        # --- NAME ---
        new_name = input(
            f"Nuevo name (actual: {record.name}) [leave blank to keep]: "
        ).strip()
        if new_name:
            try:
                normalized_name = self.normalize_name(new_name)
            except Exception as e:
                print(f"Error al normalizar el nombre: {e}")
                return
            if not normalized_name or not re.match(
                r"^[\w\sñÑáéíóúÁÉÍÓÚüÜ\-\.]+$", normalized_name
            ):
                print(
                    "Nombre inválido. Solo se permiten letras, números, espacios y algunos caracteres especiales."
                )
                return
        else:
            normalized_name = record.name

        # --- CATEGORY ---
        allowed_categories = ["tazul", "cpmp"]
        new_category = (
            input(
                f"Nueva category (actual: {record.category}, opciones: tazul/cpmp) [leave blank to keep]: "
            )
            .strip()
            .lower()
        )
        if new_category:
            if new_category not in allowed_categories:
                print("Categoría inválida. Solo se permite 'tazul' o 'cpmp'.")
                return
        else:
            new_category = record.category

        # --- IP ---
        def valid_ip_for_category(ip, category):
            try:
                parts = list(map(int, ip.split(".")))
                if len(parts) != 4:
                    return False
                if category == "cpmp":
                    return (
                        parts[0] == 192
                        and parts[1] == 168
                        and parts[2] == 16
                        and 10 <= parts[3] <= 250
                    )
                elif category == "tazul":
                    return (
                        parts[0] == 192
                        and parts[1] == 168
                        and parts[2] == 70
                        and 101 <= parts[3] <= 250
                    )
                else:
                    return False
            except Exception:
                return False

        # Nueva lógica: Si la categoría cambia y la IP se deja en blanco, validar la IP actual para la nueva categoría
        while True:
            new_ip = input(
                f"Nueva ip (actual: {record.ip}) [leave blank to keep]: "
            ).strip()
            if new_ip:
                if not valid_ip_for_category(new_ip, new_category):
                    print(
                        f"IP inválida para la categoría '{new_category}'. Intente nuevamente."
                    )
                    continue
                # Validar que la IP no esté en uso por otro registro activo en la misma categoría
                ip_in_use = False
                for r in self.registries:
                    if (
                        r is not record
                        and r.ip == new_ip
                        and r.category == new_category
                        and r.status == "active"
                    ):
                        ip_in_use = True
                        break
                if ip_in_use:
                    print(
                        "La IP ya está asignada a otro anexo activo en la misma categoría. Intente nuevamente."
                    )
                    continue
                break
            else:
                # Si la categoría cambió, validar la IP actual
                if not valid_ip_for_category(record.ip, new_category):
                    print(
                        f"La IP actual ({record.ip}) no es válida para la categoría '{new_category}'."
                    )
                    # Forzar a ingresar una IP válida
                    continue
                new_ip = record.ip
                break

        # --- OBS ---
        new_obs = input(
            f"Nueva obs (actual: {record.obs}) [leave blank to keep]: "
        ).strip()
        if not new_obs:
            new_obs = record.obs

        # Mostrar resumen y pedir confirmación
        print("\nResumen de cambios propuestos:")
        print(f"  name: {record.name} -> {normalized_name}")
        print(f"  category: {record.category} -> {new_category}")
        print(f"  ip: {record.ip} -> {new_ip}")
        print(f"  obs: {record.obs} -> {new_obs}")
        confirm = input("¿Desea guardar estos cambios? (s/n): ").strip().lower()
        if confirm != "s":
            print("Operación cancelada. No se realizaron cambios.")
            return

        # Aplicar cambios
        record.last_name = (
            record.name if normalized_name != record.name else record.last_name
        )
        record.name = normalized_name
        record.category = new_category
        record.ip = new_ip
        record.obs = new_obs
        record.updateAt = datetime.now().isoformat(sep=" ", timespec="seconds")
        self.save()
        print("Cambios guardados correctamente.")

    @staticmethod
    def normalize_name(name):
        # Quitar espacios extra y normalizar unicode, pero conservar ñ/Ñ
        name = re.sub(r"\s+", " ", name).strip()
        # Separar ñ/Ñ temporalmente para no perderlas al quitar acentos
        name = name.replace("ñ", "__enie__").replace("Ñ", "__ENIE__")
        # Normalizar unicode y quitar acentos de vocales
        name = unicodedata.normalize("NFKD", name)
        name = "".join([c for c in name if not unicodedata.combining(c)])
        # Restaurar ñ/Ñ
        name = name.replace("__enie__", "ñ").replace("__ENIE__", "Ñ")
        # Capitalizar cada palabra
        name = " ".join(w.capitalize() for w in name.split(" "))
        return name

    def load(self):
        if not os.path.exists(self.data_file):
            return []
        with open(self.data_file, "r") as f:
            return [PhoneRegistry.from_dict(x) for x in json.load(f)]

    def save(self):
        with open(self.data_file, "w") as f:
            json.dump([r.to_dict() for r in self.registries], f, indent=2)

    def list(self, category, status=None):
        filtered = [
            r
            for r in self.registries
            if (category == "all" or r.category == category)
            and (status is None or r.status == status)
        ]
        if status == "free":
            if not filtered:
                print("No free extensions found.")
                return
            for idx, r in enumerate(filtered, 1):
                print(f"--- Free Extension {idx} ---")
                for k, v in r.to_dict().items():
                    print(f"{k}: {v}")
        else:
            for r in filtered:
                print(f"{r.id}, {r.extension}, {r.ip}, {r.name}")

    def show(self, value):
        if value == "free":
            found = [r for r in self.registries if r.status == "free"]
            if not found:
                print("No free extensions found.")
                return
            for idx, r in enumerate(found, 1):
                print(f"--- Free Extension {idx} ---")
                for k, v in r.to_dict().items():
                    print(f"{k}: {v}")
            return
        found = []
        # Buscar coincidencia exacta por extensión, nombre o IP
        for r in self.registries:
            if (
                str(r.extension) == str(value)
                or r.name.lower() == value.lower()
                or r.ip == value
            ):
                found.append(r)
        if found:
            for idx, r in enumerate(found, 1):
                print(f"--- Result {idx} ---")
                for k, v in r.to_dict().items():
                    print(f"{k}: {v}")
                # Mostrar información adicional desde la PBX Yeastar, en JSON legible y separado
                api_creds = self._read_api_credentials()
                if api_creds:
                    token = self._get_api_token(api_creds)
                    if token:
                        info = self._query_extension_info(
                            r.extension, token, api_creds["pbx"]
                        )
                        if info is not None:
                            print(
                                "Información de la extensión desde la PBX (formato JSON):"
                            )
                            print(json.dumps(info, indent=2, ensure_ascii=False))
            return
        # Si no hay coincidencia exacta, buscar coincidencias parciales en el nombre
        partial = [r for r in self.registries if value.lower() in r.name.lower()]
        if partial:
            print(f"Resultados que coinciden parcialmente con '{value}':")
            for idx, r in enumerate(partial, 1):
                print(f"--- Result {idx} ---")
                for k, v in r.to_dict().items():
                    print(f"{k}: {v}")
            return
        # Si es una IP válida, mostrar mensaje especial
        if self._is_ip(value):
            print(f"IP {value} is not assigned to any registry.")
        else:
            print("No match found.")

    def _is_ip(self, value):
        parts = value.split(".")
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(p) <= 255 for p in parts)
        except ValueError:
            return False

    def _get_deny_ips(self):
        deny_file = os.path.join(os.path.dirname(__file__), "deny_ip.conf")
        deny_ips = set()
        if os.path.exists(deny_file):
            with open(deny_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        deny_ips.add(line)
        return deny_ips

    def capacity(self, mode, category=None):
        max_extension = 300
        if mode == "phone":
            used = len([r for r in self.registries if r.status == "active"])
            print(f"Used: {used}, Free: {max_extension - used}")
            print(
                f"NOTA: Se consideran dentro de la capacidad Free a los anexos en estado Free y los que aun no se han creado."
            )
        elif mode == "ip":
            deny_ips = self._get_deny_ips()

            def get_free_ips(ip_candidates, used_ips):
                return sorted(
                    set(ip_candidates) - set(used_ips) - deny_ips,
                    key=lambda x: list(map(int, x.split("."))),
                )

            if category is None or category == "all":
                cpmp_total = 241  # 16.10-16.250
                tazul_total = 150  # 70.101-70.250
                cpmp_used = [
                    r.ip
                    for r in self.registries
                    if r.category == "cpmp" and r.status == "active"
                ]
                tazul_used = [
                    r.ip
                    for r in self.registries
                    if r.category == "tazul" and r.status == "active"
                ]
                cpmp_candidates = [f"192.168.16.{i}" for i in range(10, 251)]
                tazul_candidates = [f"192.168.70.{i}" for i in range(101, 251)]
                cpmp_free = get_free_ips(cpmp_candidates, cpmp_used)
                tazul_free = get_free_ips(tazul_candidates, tazul_used)
                print(f"CPMP: Used: {len(cpmp_used)}, Free: {len(cpmp_free)}")
                print(f"TAZUL: Used: {len(tazul_used)}, Free: {len(tazul_free)}")
                print(
                    f"Total: Used: {len(cpmp_used) + len(tazul_used)}, Free: {len(cpmp_free) + len(tazul_free)}"
                )
                print("\nCPMP Free IPs:")
                print("\n".join(cpmp_free))
                print("\nTAZUL Free IPs:")
                print("\n".join(tazul_free))
            elif category == "cpmp":
                total = 241
                used = [
                    r.ip
                    for r in self.registries
                    if r.category == "cpmp" and r.status == "active"
                ]
                candidates = [f"192.168.16.{i}" for i in range(10, 251)]
                free_ips = get_free_ips(candidates, used)
                print(f"CPMP: Used: {len(used)}, Free: {len(free_ips)}")
                print("Free IPs:")
                print("\n".join(free_ips))
            elif category == "tazul":
                total = 150
                used = [
                    r.ip
                    for r in self.registries
                    if r.category == "tazul" and r.status == "active"
                ]
                candidates = [f"192.168.70.{i}" for i in range(101, 251)]
                free_ips = get_free_ips(candidates, used)
                print(f"TAZUL: Used: {len(used)}, Free: {len(free_ips)}")
                print("Free IPs:")
                print("\n".join(free_ips))

    def add(self, category):
        if category == "tzul":
            category = "tazul"
        name = input("Enter name: ")
        name = self.normalize_name(name)
        # Validar que la extensión no esté ya asignada a otro registro activo en la misma categoría
        used_ext = {
            r.extension
            for r in self.registries
            if r.category == category and r.status == "active"
        }
        used_ips = {
            r.ip
            for r in self.registries
            if r.category == category and r.status == "active"
        }
        if category == "cpmp":
            ext_candidates = [0] + list(range(120, 501))
            ip_candidates = [f"192.168.16.{i}" for i in range(10, 251)]
        else:  # tazul
            ext_candidates = list(range(601, 701))
            ip_candidates = [f"192.168.70.{i}" for i in range(101, 251)]
        ext = next((e for e in ext_candidates if e not in used_ext), None)
        ip = next((ip for ip in ip_candidates if ip not in used_ips), None)
        if ext is None or ip is None:
            print("No free extension or IP available.")
            return
        obs = input("Obs (leave blank to keep): ")
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        new_id = max([r.id for r in self.registries], default=0) + 1
        reg = PhoneRegistry(
            new_id, ext, name, "", now, now, ip, category, "active", obs
        )
        self.registries.append(reg)
        self.save()
        print(f"Added: {ext}, {ip}, {name}")

    def edit(self, value):
        for r in self.registries:
            if str(r.extension) == str(value) or r.name.lower() == value.lower():
                print("Current info:")
                for k, v in r.to_dict().items():
                    print(f"{k}: {v}")
                new_name = input("New name (leave blank to keep): ")
                if new_name:
                    new_name = self.normalize_name(new_name)
                new_obs = input("Obs (leave blank to keep): ")
                # Ya no se valida duplicidad de nombre, se permite nombres repetidos
                if new_name:
                    r.last_name = r.name
                    r.name = new_name
                if new_obs:
                    r.obs = new_obs
                r.status = "active"
                r.updateAt = datetime.now().isoformat(sep=" ", timespec="seconds")
                self.save()
                print("Updated.")

                # --- Sincronización automática con PBX Yeastar ---
                if new_name:
                    api_creds = self._read_api_credentials()
                    if api_creds:
                        token = self._get_api_token(api_creds)
                        if token:
                            status = self._update_extension_name(
                                r.extension, new_name, token, api_creds["pbx"]
                            )
                            # Mostrar información actualizada desde la PBX, en JSON legible
                            info = self._query_extension_info(
                                r.extension, token, api_creds["pbx"]
                            )
                            if info is not None:
                                print(
                                    "Información de la extensión desde la PBX (formato JSON):"
                                )
                                print(json.dumps(info, indent=2, ensure_ascii=False))
                return
        print("No match found.")

    def free(self, value):
        for r in self.registries:
            if str(r.extension) == str(value) or r.name.lower() == value.lower():
                r.last_name = r.name
                r.name = "Libre"
                r.status = "free"
                r.updateAt = datetime.now().isoformat(sep=" ", timespec="seconds")
                self.save()
                print(f"Extension {r.extension} is now free and assignable.")
                return
        print("No match found.")

    def _read_credentials(self, conf_file="credentials.conf"):
        creds = {}
        if not os.path.exists(conf_file):
            print(
                f"Archivo de credenciales '{conf_file}' no encontrado. No se puede sincronizar."
            )
            return None
        with open(conf_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    creds[k.strip()] = v.strip()
        # No validamos aquí los campos, porque puede ser usado para TFTP o API
        return creds

    def _query_extension_info(self, extid, token, pbx_url):
        url = f"{pbx_url}/api/v1.1.0/extension/query?token={token}"
        payload = {"extid": str(extid)}
        try:
            resp = requests.post(url, json=payload, verify=False, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data
        except Exception as e:
            print(f"Error consultando extensión en PBX: {e}")
            return None

    def _read_api_credentials(self, conf_file="credentials.conf"):
        creds = self._read_credentials(conf_file)
        required = {"PBX_API", "USER_API", "PASS_API"}
        if not creds or not required.issubset(creds):
            print(
                f"Faltan campos de API en '{conf_file}'. Se requieren: {', '.join(required)}"
            )
            return None
        return {
            "pbx": creds["PBX_API"],
            "user": creds["USER_API"],
            "pass": creds["PASS_API"],
        }

    def _get_api_token(self, api_creds):
        url = f"{api_creds['pbx']}/api/v1.1.0/login"
        payload = {"username": api_creds["user"], "password": api_creds["pass"]}
        try:
            resp = requests.post(url, json=payload, verify=False, timeout=10)
            resp.raise_for_status()
            token = resp.json().get("token")
            if not token:
                print("No se pudo obtener el token de la API. Respuesta:", resp.text)
            return token
        except Exception as e:
            print(f"Error obteniendo token de la API Yeastar: {e}")
            return None

    def _update_extension_name(self, extid, username, token, pbx_url):
        url = f"{pbx_url}/api/v1.1.0/extension/update?token={token}"
        payload = {"extid": str(extid), "username": username}
        try:
            resp = requests.post(url, json=payload, verify=False, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            print("Respuesta de la PBX al actualizar nombre:", data)
            return data
        except Exception as e:
            print(f"Error actualizando extensión en PBX: {e}")
            return None

    def generate(self):
        import datetime
        import os
        import re
        import subprocess

        import openpyxl
        from openpyxl.styles import Font

        filename_xml = "result/RemotePhonebook.xml"
        filename_xlsx = f"result/lacaja_lista_anexos_{datetime.datetime.now().strftime('%d%m%Y')}.xlsx"
        print("1. phonebook file with automatic upload to s300pbx")
        print("2. phone_list in format excel, with cpmp and tazul sheets")
        opt = input("Choose option: ")
        if opt == "1":
            print("Generando el archivo " + filename_xml + " ...")
            xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
            xml += "<YealinkIPPhoneBook>\n<Title>Yealink</Title>\n"
            xml += '<Menu Name="CPMP">\n'
            for r in self.registries:
                if (
                    r.name == "Libre"
                    or re.match(r"^123[4-6]$", str(r.name))
                    or r.name == "Luis Terrel"
                    or r.name == 901
                ):
                    continue
                normalized_name = self.normalize_name(r.name)
                xml += f'<Unit Name="{normalized_name}" Phone1="{r.extension}" Phone2="" Phone3="" default_phone="Resource:"/>\n'
            xml += "</Menu>\n"
            xml += "</YealinkIPPhoneBook>\n"
            os.makedirs(os.path.dirname(filename_xml), exist_ok=True)
            with open(filename_xml, "w", encoding="utf-8") as f:
                f.write(xml)
            # Cambiar permisos a 777
            try:
                os.chmod(filename_xml, 0o777)
            except Exception as e:
                print(f"Advertencia: No se pudo cambiar permisos a 777: {e}")
            print("El archivo " + filename_xml + " ha sido generado")
            # --- Sincronización TFTP ---
            creds = self._read_credentials()
            if creds is None:
                print(
                    "No se puede sincronizar automáticamente. Realice la carga manual del archivo."
                )
                return
            # Test SSH connection
            print(f"Probando conexión SSH a {creds['HOST']} ...")
            try:
                test_cmd = [
                    "sshpass",
                    "-p",
                    creds["PASS"],
                    "ssh",
                    "-o",
                    "ConnectTimeout=5",
                    creds["HOST"],
                    "echo",
                    "ok",
                ]
                result = subprocess.run(
                    test_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=7
                )
                if b"ok" not in result.stdout:
                    raise Exception(result.stderr.decode())
            except Exception as e:
                print(
                    f"No hay conexión SSH con el servidor. Debe cargar manualmente el archivo: {filename_xml}\nDetalle: {e}"
                )
                return
            # Rsync
            print("Sincronizando archivo al servidor TFTP ...")
            rsync_cmd = [
                "sshpass",
                "-p",
                creds["PASS"],
                "rsync",
                "--progress",
                "-avz",
                filename_xml,
                "-e",
                f"ssh -o ConnectTimeout=5",
                f"{creds['HOST']}:{creds['DEST_PATH']}",
            ]
            try:
                subprocess.run(rsync_cmd, check=True)
                print("Sincronización completada con éxito.")
            except Exception as e:
                print(
                    f"Error al sincronizar el archivo: {e}\nDebe cargar manualmente el archivo: {filename_xml}"
                )
        elif opt == "2":
            print("Generando Excel de anexos...")
            wb = openpyxl.Workbook()
            ws = wb.active
            ws["B1"] = "ID"
            ws["C1"] = "NUMERO"
            ws["D1"] = "NOMBRE"
            ws["B1"].font = Font(bold=True, size=12)
            ws["C1"].font = Font(bold=True, size=12)
            ws["D1"].font = Font(bold=True, size=12)
            row_pos = 2
            col_pos = 2
            index = 1
            for r in self.registries:
                ws.cell(row=row_pos, column=col_pos, value=index)
                ws.cell(row=row_pos, column=col_pos + 1, value=r.extension)
                ws.cell(row=row_pos, column=col_pos + 2, value=r.name)
                row_pos += 1
                index += 1
            os.makedirs(os.path.dirname(filename_xlsx), exist_ok=True)
            wb.save(filename_xlsx)
            print(f"Generate document list extensions cpmp {filename_xlsx}")
        else:
            print("Invalid option.")


def main():
    pb = PhoneBook()
    if len(sys.argv) < 2:
        print("""
Uso: phoneadm <comando> [argumentos]

Comandos disponibles:
  list [segmento] [status]  Lista registros del segmento (all, cpmp, tazul). Si se agrega 'free', muestra solo los libres.
  show <extension>          Muestra información de un registro por extensión, nombre o IP (búsqueda exacta o parcial)
  capacity phone            Muestra la capacidad de anexos usados y libres
  capacity ip [segmento]    Muestra las IPs libres por segmento (all, cpmp, tazul), excluyendo deny_ip.conf, esto considera como libres aquellos registros en estado Free.
  add <segmento>            Agrega un nuevo registro (segmento: cpmp, tazul)
  edit <extension>          Edita un registro por extensión o nombre
  change <ext|name>         Modifica múltiples campos de un anexo existente (name, category, ip, obs)
                            Uso: ./phoneadm.py change exten|name_exten
                            Para cada campo, se mostrará el valor actual y podrá dejarlo en blanco para mantenerlo.
                            Solo se permiten categorías: tazul, cpmp. El segmento de IP debe corresponder a la categoría.
                            Se mostrará un resumen de los cambios antes de guardar.
  free <extension>          Libera un registro por extensión o nombre (lo marca como Libre)
  generate                  Genera archivos de phonebook XML o Excel interactivo

Ejemplos:
  phoneadm list cpmp
  phoneadm list cpmp free
  phoneadm show 123
  phoneadm show free
  phoneadm show Franz
  phoneadm capacity ip tazul
  phoneadm capacity phone
  phoneadm add cpmp
  phoneadm edit "Mesa de partes"
  phoneadm change 101
  phoneadm change "Julio Campos"
  phoneadm free 122
  phoneadm generate
""")
        return
    cmd = sys.argv[1]
    if cmd == "list":
        cat = sys.argv[2] if len(sys.argv) > 2 else "all"
        status = sys.argv[3] if len(sys.argv) > 3 else None
        pb.list(cat, status)
    elif cmd == "show" and len(sys.argv) > 2:
        pb.show(sys.argv[2])
    elif cmd == "capacity" and len(sys.argv) > 2:
        if sys.argv[2] == "ip":
            cat = sys.argv[3] if len(sys.argv) > 3 else "all"
            pb.capacity("ip", cat)
        else:
            pb.capacity(sys.argv[2])
    elif cmd == "add" and len(sys.argv) > 2:
        pb.add(sys.argv[2])
    elif cmd == "edit" and len(sys.argv) > 2:
        pb.edit(sys.argv[2])
    elif cmd == "free" and len(sys.argv) > 2:
        pb.free(sys.argv[2])
    elif cmd == "change" and len(sys.argv) > 2:
        pb.change(sys.argv[2])
    elif cmd == "generate":
        pb.generate()
    else:
        print("Unknown command or missing arguments.")


if __name__ == "__main__":
    main()
