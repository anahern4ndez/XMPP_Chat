from client import *

if __name__ == '__main__':
    while True:
        print("Ingrese la acción que desea realizar: \n\t1. Registrarse \n\t2. Iniciar sesión. \n\t3. Salir.")
        opcion = input("> ")
        username = input("Ingrese el nombre de usuario (SIN dominio): ")
        password = input("Ingrese la contraseña de usuario: ")
        if opcion == "1":
            user_register(username, password)
        elif opcion == "2":
            user_client = user_login(username, password)
            while True:
                print("Ingrese la acción que desea realizar: \
                    \n\t1. Enviar un mensaje a alguien \n\t2. Eliminar usuario \n\t3. Mostrar todos mis contactos y su estado \n\t4. Agregar a alguien a mis contactos\
                    \n\t5. Mostrar detalles de un usuario \n\t6. Crear un grupo \n\t7. Enviar mensaje a un grupo existente \n\t8. Definir mensaje de presencia. \
                    \n\t9. Enviar una notificación. \n\t10. Enviar un archivo\
                    \n\t11. Cerrar sesión.")
                inop = input("> ")
                if inop == "1":
                    msg = input("Ingrese mensaje a enviar: ")
                    recipient = input("Ingrese el username del usuario recipiente: ")
                    user_client.send_msg(recipient, msg)
                elif inop =="11":
                    user_client.disconnect_user()
                    break
        elif opcion == "3":
            break
        else:
            print("Opción incorrecta. Intente de nuevo. ")  



    

    """
        User unregister 
    """
    # username = "anah@redes2020.xyz"
    # password = "hola"
    # jid = xmpp.JID(username)
    # xmpp_cli = xmpp.Client(jid.getDomain())
    # xmpp_cli.connect()
    # # xmpp_cli.auth(jid.node, password, jid.resource)
    # if xmpp.features.unregister(xmpp_cli,""):
    #     sys.stderr.write('Successfully deleted user.\n')
    #     sys.exit(0)
    # else:
    #     sys.stderr.write('Error\n')
    #     sys.exit(1)

