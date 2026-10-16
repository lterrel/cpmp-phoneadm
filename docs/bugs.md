Fri Jan 16 11:19:48 EST 2026
- Si ingresas un nombre que ya existe registrado, no es posible actualizar el nombre del anexo i.e:
```
> ./phoneadm.py edit "604"
Current info:
id: 225
extension: 604
name: Irma Egoavil
last_name:
createAt: 2025-09-03 00:00:00
updateAt: 2025-09-03 00:00:00
ip: 192.168.70.104
category: tazul
status: active
obs:
New name (leave blank to keep): Libre
Obs (leave blank to keep):
A registry with the name 'Libre' already exists in tazul.
```
## fixed

Thu Jan 22 10:49:39 EST 2026

- Si ingresas un nombre por ejemplo Gustavo Aramayo este se debe dar formato automaticamente en formato estandar 
  manteniendo el nombre y apellido, para caracteres con acento y ene se debe normalizar de forma adecuada.
### NOTAS:
* Se mantiene el ingreso de N palabras, pero se capitaliza, no se incorpora acentos solo enies.
## fixed
