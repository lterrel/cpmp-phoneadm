# Debug for put and refresh phonebook on yeastar pbx

Check if donwload work for remote phonebook:

```shell
 curl -O tftp://192.168.15.200/upload/autopfile/RemotePhonebook.xml
```

Example upload file: 

```shell
curl -T file tftp://192.168.15.200/upload/autopfile/
```

Default route where save file when upload via gui:

```shell
/ysdisk/tftpboot/upload/autopfile
/ysdisk/tftpboot/ (root)
```
