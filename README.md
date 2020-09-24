# XMPP_Chat
 
 
## Descripción

Este proyecto consiste en la implementación de un chat multi-usuario utilizado el protocolo XMPP. Se incluyen funcionalidades como:
 1. Enviar un mensaje a alguien 
 2. Mostrar a todos los usuarios existentes 
 3. Mostrar todos mis contactos y su estado 
 4. Agregar a alguien a mis contactos                    
 5. Mostrar detalles de un usuario 
 6. Crear/unirse a un grupo 
 7. Enviar mensaje a un grupo 
 8. Definir mensaje de presencia.                     
 9. Enviar un archivo 
 10. Eliminar usuario                    
 11. Cerrar sesión.

En secciones siguientes se explicará el funcionamiento de cada aspecto implementado. 

## Primeros pasos

### Requerimientos 

Este proyecto requiere la previa instalación de python>=3.8 y pip>=20.2.2. Adicionalmente, se requieren unas librerías de implementación de XMPP, todas estas dependencias se pueden instalar corriendo el siguiente comando: `pip install -r requirements.txt`. En el archivo requirements.txt se encuentran las dependencias necesarias y sus versiones. Un aspecto importante es que las siguientes librerías deben tener las siguientes versiones obligatoriamente:
1. sleexmpp=1.3.1
2. pyasn1==0.3.7
3. pyasn1-modules==0.1.5

### Instalación

1. Clona este repositorio utilizando `https://github.com/her17138/XMPP_Chat.git`
2. Corre el comando `pip install -r requirements.txt` para instalar las librerías necesarias con sus versiones respectivas para que este proyecto funcione.
3. Corre el comando `python3 main.py` para correr la implementación de un cliente con el protocolo XMPP.

## Estructura del proyecto 

### Directorios

En el directorio de `files_received` se depositan todos los archivos que han sido recibido de parte de otros clientes. 

### Archivos
#### main.py

Este archivo contiene el menú principal que se le muestra al usuario, hace displays de los prints y los inputs para llamar a las funciones definidas en `client.py`.

#### client.py

Este archivo contiene la implementación del cliente en sí. A continuación se explicará a fondo los aspectos de la implmentación previamente mencionados. 

1. Enviar un mensaje a alguien</br>


2. Mostrar a todos los usuarios existentes </br>

3. Mostrar a todos mis contactos </br>

4. Agregar un usuario a mis contactos </br>

5. Mostrar a todos los usuarios existentes </br>

6. Mostrar a todos los usuarios existentes </br>

7. Mostrar a todos los usuarios existentes </br>

8. Mostrar a todos los usuarios existentes </br>

9. Mostrar a todos los usuarios existentes </br>

10. Eliminar un usuario </br>

11. Cerrar sesión </br>



## Features
- 🐍 **Python** — Lenguaje sobre el cual se realizó la implementación.
- 📬 **XMPP**  — Protocolo de envío de mensajes.
