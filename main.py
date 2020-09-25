from client import *
from pathlib import Path
from tkinter import *
from tkinter import filedialog


# # Ideally use optparse or argparse to get JID,
# # password, and log level.

logging.basicConfig(level=logging.ERROR,
                    format='%(levelname)-8s %(message)s')
# logging.disable()

while True:
    print("Ingrese la acción que desea realizar: \n\t1. Registrarse \n\t2. Iniciar sesión. \n\t3. Salir.")
    opcion = input("> ")
    # opcion = "2"
    if opcion == "3":
        print("Bye!")
        break
    username = input("Ingrese el nombre de usuario (SIN dominio): ")+"@redes2020.xyz"
    password = input("Ingrese la contraseña de usuario: ")
    # username = "anah@redes2020.xyz"
    # password = "hola"
    if opcion == "1":
        user_register(username, password)
    elif opcion == "2":
        print("Verificando datos...")
        user_client = user_login(username, password)
        if user_client:
            while True:
                print("Ingrese la acción que desea realizar: \
                    \n\t1. Enviar un mensaje a alguien \n\t2. Mostrar a todos los usuarios existentes \n\t3. Mostrar todos mis contactos y su estado \n\t4. Agregar a alguien a mis contactos\
                    \n\t5. Mostrar detalles de un usuario \n\t6. Crear/unirse a un grupo \n\t7. Enviar mensaje a un grupo \n\t8. Definir mensaje de presencia. \
                    \n\t9. Enviar un archivo \n\t10. Eliminar usuario\
                    \n\t11. Cerrar sesión.")
                inop = input("> ")
                if inop == "1":
                    msg = input("Ingrese mensaje a enviar: ")
                    recipient = input("Ingrese el username del usuario recipiente (SIN dominio): ")+"@redes2020.xyz"
                    user_client.send_msg(recipient, msg)
                elif inop == "2":
                    print("Usuarios registrados en el servidor:")
                    print(user_client.get_all_users())
                elif inop == "3":
                    contacts = user_client.get_my_contacts()
                    print("\nMis contactos:", contacts)
                elif inop == "4":
                    new_contact = input("Ingrese el username del usuario a agregar (SIN dominio): ")+"@redes2020.xyz"
                    user_client.add_contact(new_contact)
                elif inop == "5":
                    search = input("Ingrese la información del usuario: ")
                    print("A continuación, ingrese y (o dé enter) si se desea buscar la información ingresada por los campos respectivos, ingrese n si no se desea buscar por ese campo. Puede buscar por más de un campo a la vez.")
                    user_username = input("¿Buscar entre los usernames disponibles? (Y/n) ").upper()
                    email = input("¿Buscar entre los emails disponibles? (Y/n) ").upper()
                    name = input("¿Buscar entre los nombres disponibles? (Y/n) ").upper()
                    info = user_client.get_user_info(
                        search,
                        username = True if user_username == "Y" or not user_username else False,
                        email = True if email == "Y" or not email else False,
                        name = True if name == "Y" or not name else False,
                    )
                    if info:
                        print("Usuarios encontrados: \n"+info)
                    else:
                        print("No se han encontrado usuarios con esa información.")
                elif inop == "6":
                    gc_name = input("Ingrese el nombre del grupo (SIN dominio): ") + "@conference.redes2020.xyz"
                    nick = input("Si desea un nombre en el chatroom diferente a su username, ingréselo ahora (enter para obviar): ")
                    user_client.join_group(gc_name, nick)
                elif inop == "7":
                    gc = input("Ingrese el grupo a enviar el mensaje (SIN dominio): ")+ "@conference.redes2020.xyz"
                    msg = input("Ingrese mensaje a enviar: ")
                    user_client.send_msg_to_room(gc, msg)
                elif inop == "8":
                    new_status = input("Ingrese el nuevo mensaje a enviar con el presence: ")
                    user_client.update_presence(new_status)
                elif inop == "9":
                    recipient = input("Ingrese el usuario a recibir el archivo (SIN dominio): ")+"@redes2020.xyz"
                    # filename = input("Ingrese nombre del archivo (SIN extension): ")
                    window = Tk()
                    window.withdraw()
                    allowed_formats = { # solo este tipo de archivos se pueden enviar, otro tipo de multimedia no está testeado
                        "csv": { 'mime': 'text/csv', 'tuple': ("CSV files", "*.csv")},
                        "txt": { 'mime': 'text/plain', 'tuple': ("Text files", "*.txt")},
                        "png": { 'mime': 'image/png', 'tuple': ("PNG files", "*.png")},
                        "jpeg": { 'mime': 'image/jpeg', 'tuple': ("Jpeg files", "*.jpeg")},
                        "jpeg": { 'mime': 'image/jpeg', 'tuple': ("Jpg files", "*.jpg")},
                        "pdf": { 'mime': 'application/pd', 'tuple': ("PDF files", "*.pdf")}
                    } # de preferencia, que también se reciban archivos de este tipo
                    a, b, c, d, e = [value["tuple"] for key, value in allowed_formats.items()]
                    window.update()
                    fullpath = filedialog.askopenfilename(initialdir = ".", 
                        title = "Select a File",
                        filetypes = (a,b,c,d,e)) 

                    # obtención de información del archivo
                    file_info = Path(fullpath).stat()
                    size = file_info.st_size
                    path_dirs = fullpath.split('/')
                    name = path_dirs[len(path_dirs) -1]
                    try:
                        file_type = name.split(".")[1]
                        print("File attributes: \n\tName: {}, size: {} bytes, type: {}".format(name, size, file_type))
                        # filename = "test_img.png"
                    except IndexError:
                        print("El archivo seleccionado debe tener la extensión en su nombre.")
                        continue
                    user_client.send_file_request(fullpath,recipient, mime_type=allowed_formats[file_type]['mime'], size = size) # comenzar el envío de archivo
                elif inop == "10":
                    user_client.delete_user()
                    user_client.disconnect_user()
                    break
                elif inop =="11":
                    user_client.disconnect_user()
                    break
        else:
            print("Credenciales incorrectas. Intente de nuevo.")
    else:
        print("Opción incorrecta. Intente de nuevo. ")  