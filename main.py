from client import *


# # Ideally use optparse or argparse to get JID,
# # password, and log level.

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)-8s %(message)s')

while True:
    print("Ingrese la acción que desea realizar: \n\t1. Registrarse \n\t2. Iniciar sesión. \n\t3. Salir.")
    opcion = input("> ")
    if opcion == "3":
        print("Bye!")
        break
    username = input("Ingrese el nombre de usuario (SIN dominio): ")+"@redes2020.xyz"
    password = input("Ingrese la contraseña de usuario: ")
    if opcion == "1":
        user_register(username, password)
    elif opcion == "2":
        print("Verificando datos...")
        user_client = user_login(username, password)
        if user_client:
            while True:
                print("Ingrese la acción que desea realizar: \
                    \n\t1. Enviar un mensaje a alguien \n\t2. Eliminar usuario \n\t3. Mostrar todos mis contactos y su estado \n\t4. Agregar a alguien a mis contactos\
                    \n\t5. Mostrar detalles de un usuario \n\t6. Crear un grupo \n\t7. Enviar mensaje a un grupo existente \n\t8. Definir mensaje de presencia. \
                    \n\t9. Enviar una notificación. \n\t10. Enviar un archivo\
                    \n\t11. Cerrar sesión.")
                inop = input("> ")
                if inop == "1":
                    # 100% funcional
                    msg = input("Ingrese mensaje a enviar: ")
                    recipient = input("Ingrese el username del usuario recipiente: ")
                    user_client.send_msg(recipient, msg)
                elif inop == "2":
                    # 100% funcional
                    user_client.delete_user()
                    user_client.disconnect_user()
                elif inop =="11":
                    user_client.disconnect_user()
                    break
        else:
            print("Credenciales incorrectas. Intente de nuevo.")
    else:
        print("Opción incorrecta. Intente de nuevo. ")  