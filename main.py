from client import *


# # Ideally use optparse or argparse to get JID,
# # password, and log level.

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)-8s %(message)s')

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
                    \n\t5. Mostrar detalles de un usuario \n\t6. Crear un grupo \n\t7. Enviar mensaje a un grupo existente \n\t8. Definir mensaje de presencia. \
                    \n\t9. Enviar una notificación. \n\t10. Enviar un archivo \n\t11. Eliminar usuario\
                    \n\t12. Cerrar sesión.")
                inop = input("> ")
                if inop == "1":
                    # 100% funcional
                    msg = input("Ingrese mensaje a enviar: ")
                    recipient = input("Ingrese el username del usuario recipiente: ")+"@redes2020.xyz"
                    user_client.send_msg(recipient, msg)
                elif inop == "2":
                    # 100% funcional
                    print("Usuarios registrados en el servidor:")
                    print(user_client.get_all_users())
                elif inop == "3":
                    # 100% funcional
                    contacts = user_client.get_my_contacts()
                    print("\nMis contactos:", contacts)
                elif inop == "4":
                    # 100% funcional
                    new_contact = input("Ingrese el username del usuario a agregar (SIN dominio): ")+"@redes2020.xyz"
                    user_client.add_contact(new_contact)
                elif inop == "5":
                    # 100% funcional
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
                    gc_name = input("Ingrese el nombre del grupo: ") + "@conference.redes2020.xyz"
                    # send_msg_to_room()
                    user_client.join_group(gc_name)
                elif inop == "7":
                    gc = input("Ingrese el grupo a enviar el mensaje: ")
                    msg = input("Ingrese mensaje a enviar: ")
                    user_client.send_msg_to_room(gc, msg)
                elif inop == "10":
                    user_client.send_file("./chavo_x.png", "mafprueba@redes2020.xyz")
                elif inop == "11":
                    # 100% funcional
                    user_client.delete_user()
                    user_client.disconnect_user()
                elif inop =="12":
                    # 100% funcional
                    user_client.disconnect_user()
                    break
        else:
            print("Credenciales incorrectas. Intente de nuevo.")
    else:
        print("Opción incorrecta. Intente de nuevo. ")  