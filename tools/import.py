#!/usr/bin/env python3
import csv
import json
from datetime import datetime

input_file = "data.txt"
output_file = "phoneadm_data.json"
now = "2025-09-03 00:00:00"
result = []
id_counter = 222

with open(input_file, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ext = row['ANEXO ACTUAL'].strip()
        name = row['NOMBRE'].strip()
        ip = row['IP'].strip()
        if ip == "NONE":
            continue
        # Cambia el tercer octeto de 15 a 16 si corresponde
        ip_parts = ip.split('.')
        if len(ip_parts) == 4 and ip_parts[2] == '15':
            ip_parts[2] = '16'
            ip = '.'.join(ip_parts)
        # Segmento
        category = "cpmp"
        # Status
        status = "free" if name.lower() == "libre" else "active"
        # Construye el registro
        reg = {
            "id": id_counter,
            "extension": int(ext),
            "name": name,
            "last_name": "",
            "createAt": now,
            "updateAt": now,
            "ip": ip,
            "category": category,
            "status": status,
            "obs": ""
        }
        result.append(reg)
        id_counter += 1

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Procesados {len(result)} registros en {output_file}")
