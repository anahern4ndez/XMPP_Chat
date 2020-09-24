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
 10. Envío de notificaciones
 11. Eliminar usuario                    
 12. Cerrar sesión.
 13. Registrar un usuario
 14. Iniciar sesión.

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

Este archivo contiene la implementación del cliente en sí; la clase Client contiene todos los métodos y atributos necesarios para su funcionamiento, exceptuando el método de registro de cliente (esto se realizó con la librería xmpppy, no sleekxmpp) y el método de login. A continuación se explicará a fondo los aspectos de la implmentación previamente mencionados. 

##### 1. Enviar un mensaje a alguien 

Para enviar un mensaje, se ingresa solo la parte de usuario del JID (sin el dominio) y seguidamente se ingresa el mensaje qu se desea enviar. El mensaje puede ser enviado a alguien que esté dentro de los contactos del usuario o no. 

##### 2. Mostrar a todos los usuarios existentes 

Se realiza una búsqueda de todos los usuarios registrados en el servidor y se devuelve una lista del username, JID, email (si tiene uno) y nombre (si tiene uno). 

##### 3. Mostrar a todos mis contactos 

Se hace una búsqueda del roster del cliente; todos aquellos usuarios que tengan un "subscription = both" con el cliente presente. 

##### 4. Agregar un usuario a mis contactos 

Por default, se tiene configurado que este cliente acepte todas las solicitudes de "amistad" automáticamente, no se implementó un handler en caso la solicitud sea rechazada. 

##### 5. Mostrar detalles de un usuario 

Se le da opción al usuario de ingresar qué parámetros de búsqueda desea (Username/Name/Email), se puso como default que se busquen con todos los parámetros y se pide al usuario una frase o dato a buscar. 

##### 6. Crear/unirse a un grupo 

Se le pide al usuario que ingrese un nombre de grupo (sin el dominio), en caso que este grupo no exista, se creará y el usuario ingresará a este chat room. Para saber si el ingreso fue exitoso, debe aparecer una notificación de '<username del cliente> ha ingresado al chat.' De lo contrario se asume que ocurrió un error con el ingreso (no se hará display de este), en caso esto suceda, se puede intentar volver a unir al grupo con un nickname distinto al default. En las pruebas con usuarios específicos usar el nickname default (el cual es el username del cliente) demostró ser un problema una baja cantidad de veces. 

##### 7. Enviar mensaje a un grupo 

La mejor ruta de acción es ingresar al grupo antes de intentar enviar un mensaje al mismo, sin embargo, se realiza una verificación si el cliente se ha al grupo y ya está registrado o no y en caso no lo esté se solicita el ingreso y seguidamente se envía el mensaje. 

##### 8. Definir mensaje de presencia 

El mensaje de presencia se definió como el "mensaje de estado" de un usuario. Estos no son persistentes en el servidor por lo que cada vez que se corre `main.py`, todos los mensajes de presencia previamente registrados quedan borrados. Cuando un contacto redefine su mensaje de presencia, se recibe el Presence stanza y se activa una notificación informando al cliente quién ha cambiado su presence a cuál mensaje. Este mensaje, mientras dure la sesión, queda guardado y se puede obtener los actuales mensajes de presencia de todos mis contactos al usar la opción 3 de esta lista; los contactos que no hayan redefinido su mensaje, no tendrán uno. 

Cabe destacar que cuando el cliente define un mensaje de presencia, este mensaje solo se envía a sus contactos, y en caso esté registrado a algún chat grupal, su mensaje de presencia se recibirá solo si se ha redefinido previo a su ingreso (porque cuando se une se muestra el mensaje de presencia que definió), pero si se redefine después que ha ingresado, los integrantes del chat no recibirán esta notificación. 

##### 9. Enviar un archivo 

Se abre una ventana (con ayuda de la librería tkinter) en la cual se selecciona el archivo a enviar (en caso ser el sender). Se prefiere que los archivos a enviar sean de tipo csv, pdf, jpg, jpeg, png o txt; cualquier otro formato no ha sido testeado. Se utilizó el plugin de xep_0096 y xep_0095 para realizar el file transfer negotiation, al recibir el accept del receptor se abre un bytestream, por el cual se envía el archivo por batches o chunks. A pesar que en la negociación están los protocolos SOCKS5 e IBB (In-band Bytestream) en el cliente únicamente se implementó IBB, por lo que tanto el emisor como el receptor deben tener implementado - por lo menos - este protocolo para envío de archivos. 

Como default, se tiene que el cliente siempre aceptará los requests (offers de la negociación) automáticamente, por lo que no hay un prompt para que el usuario ingrese esto. 

##### 10. Envío de notificaciones.  

Las notificaciones se despliegan como prints con el prefijo *NOTIFICACION*, el cliente realiza notificaciones para los siguientes eventos:
- Cuando un contacto inicia sesión. 
- Cuando un contacto se desconecta.
- Cuando un contacto cambia su mensaje de presencia. 
- Cuando alguien ingresa a un chat grupal en el que estoy. 
- Cuando alguien envía un mensaje al chat grupal en el que estoy. 
- Cuando alguien me envía un mensaje. 


##### 11. Eliminar un usuario 

Si el usuario lo desea, puede eliminar su usuario permanentemente del registro del servidor. Luego de seleccionar esta opción, lo regresa al menú de inicio y debe autenticarse nuevamente. 

##### 12. Cerrar sesión 

El usuario se desconecta. Es regresado al menú inicial y debe autenticarse de nuevo. 

##### 13. Registrar un usuario 

Para este caso se asume que el usuario a registrar no existe ya en el servidor, se utiliza xmpppy para realizar el registro de un nuevo usuario. 

##### 14. Iniciar sesión

Cuando se inicia sesión, se hace saber al usuario que se están verificando los datos, en el momento en el que se recibe un auth_success o session_start, se le permite acceder al segundo menú de inicio. De lo contrario - en caso de un auth_fail, no se le permite el acceso a las otras opciones y debe autenticarse de nuevo. 

## Features
- 🐍 Python — Lenguaje sobre el cual se realizó la implementación.
- 📬 XMPP  — Protocolo de envío de mensajes.
