import logging
import xmpp, sys
import sleekxmpp
from sleekxmpp.exceptions import IqError, IqTimeout, XMPPError
from sleekxmpp.xmlstream import XMLStream, JID
import ssl
import xml.etree.ElementTree as ET
from sleekxmpp.xmlstream.stanzabase import multifactory, ElementBase
from sleekxmpp.xmlstream.tostring import tostring
import base64
from sleekxmpp.plugins.xep_0096 import stanza, File

SOCKS5 = 'http://jabber.org/protocol/bytestreams'
IBB = 'http://jabber.org/protocol/ibb'

class Client(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.logged_in = -1
        self.instance_name = JID(jid).bare # para guardar el JID  de este usuario
        self.my_contacts = {} # para guardar la información de mis contactos
        self.files_recv = [] # para guardar temporalmente un archivo que se está recibiendo (guarda data y metadata)

        self.add_event_handler("session_start", self.session_start, threaded=False, disposable=True)
        self.add_event_handler("message", self.receive_message, threaded=True, disposable=False)
        self.add_event_handler("failed_auth", self.on_failed_auth)
        self.add_event_handler("got_offline", self.contact_sign_out)
        self.add_event_handler("presence_unavailable", self.contact_sign_out)
        self.add_event_handler("got_online", self.contact_sign_in)
        self.add_event_handler("roster_update", self.roster_update)
        self.add_event_handler("changed_status", self.changed_status)
        self.add_event_handler("si_request", self.file_transfer_req)
        # self.add_event_handler("presence_subscribed", self.added_contact) # server envia mensaje de add contact success
        self.add_event_handler("ibb_stream_start", self.stream_opened, threaded=True)
        self.add_event_handler("ibb_stream_data", self.stream_data)
        self.add_event_handler("ibb_stream_end", self.stream_end)
        self.add_event_handler("groupchat_presence", self.groupchat_notif)
        
        # Registro de plugins 
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0199') # XMPP Ping
        self.register_plugin('xep_0050')
        self.register_plugin('xep_0133')
        self.register_plugin('xep_0045') # MUC
        # file transfer
        self.register_plugin('xep_0047' , {
            'auto_accept': True
        }) # In-band Bytestreams 
        self.register_plugin('xep_0065')
        self.register_plugin('xep_0020')
        self.register_plugin('xep_0095')
        self.register_plugin('xep_0096') # SI File Transfer

        # If you are working with an OpenFire server, you will
        # need to use a different SSL version:
        self.ssl_version = ssl.PROTOCOL_TLS

        if self.connect():
            print("Opened XMPP Connection")
            self.process(block=False)
        else:
            raise Exception("Unable to connect to server.")
    
    """
                            ------------------      Métodos de inicialización del cliente, manejo de autenticación o de presencia. 
                                                    Responden a eventos de session_start, failed_auth, roster_update, changed_status, etc     -------------------
    """
    def roster_update(self, event):
        # se agrega un usuario que no estaba en mis contactos
        for contact in self.client_roster.keys():
            contactjid = JID(contact)
            if (contactjid.bare not in self.my_contacts.keys()) and (contactjid.domain != "conference.redes2020.xyz"): # se excluye los users en el roster que sean grupos (chats)
                self.my_contacts[contactjid.bare] = {'state': "Offline", 'fulljid': "", 'status_msg': ''}
        # se verifica si algun usuario se eliminó y se actualiza la lista de acorde
        deleted_clients = []
        for mycontact in self.my_contacts.keys():
            if mycontact not in self.client_roster.keys():
                deleted_clients.append(mycontact)
        for delc in deleted_clients:
            del self.my_contacts[delc]

    def session_start(self, event):
        try:
            self.send_presence() # se envía presence inicial al server
            self.get_roster(block = True, timeout = 5)
            # parse del roster para obtener estado de los contactos 
            # print("contacts in client roster", self.client_roster)
            for contact in self.client_roster.keys():
                self.my_contacts[JID(contact).bare] = {'state': "Offline", 'fulljid': "", 'status_msg': ''}
            # print("Joined rooms:", ", ".join(list(self.plugin['xep_0045'].getJoinedRooms())))
            self.logged_in = 0 # una vez esté loggeado correctamente, se hace saber al main.py que ya puede imprimir el menú siguiente
            

        except IqError as err:
            logging.error('There was an error getting the roster')
            logging.error(err.iq['error']['condition'])
            self.disconnect()
        except IqTimeout:
            logging.error('Server is taking too long to respond')
            self.disconnect()
    
    def on_failed_auth(self, event):
        # en caso las credenciales ingresadas con el usuario sean incorrectas, no puede iniciar sesión. 
        self.logged_in = 1

    def disconnect_user(self):
        """ 
            User sign out 
        """
        # Using wait=True ensures that the send queue will be
        # emptied before ending the session.
        print("Disconnecting. Waiting for send queue to empty...")
        self.disconnect(wait=True)

    def delete_user(self):
        """ 
            User unregister 
        """
        remov_obj = ET.fromstring(
            "<query xmlns='jabber:iq:register'>\
                <remove/>\
            </query>")
        delete_req = self.make_iq_set(sub=remov_obj) # se envía stanza a server indicando que se desea eliminar este usuario
        try:
            delete_req.send(now=True)
            print("User successfully deleted")
        except IqError as e:
            print("Deleting failed.", e)
        except IqTimeout:
            raise Exception("Unable to reach server.")

    def update_presence(self, new_status):
        # se envía una notificación a todos los demás de mi roster que he cambiado mi mensaje de estado.
        self.send_presence(
            pshow="chat",
            pstatus=new_status
        )
        
    def changed_status(self, event):
        # recepción de evento en el que alguno de mis contactos ha actualizado su mensaje de presencia. 
        from_usr = JID(event['from'])
        if event['status'] and from_usr.domain != 'conference.redes2020.xyz': # si el mensaje de presencia trae un estado, realizar el cambio y la notificacion
            self.my_contacts[from_usr.bare]['status_msg'] = event['status']
            print("NOTIFICACION: {} ha cambiado el mensaje de su estado a '{}'".format(from_usr.user, event['status']))
    
    """
                                ------------------      Métodos de manejo de mensajes individuales. -------------------
    """

    def send_msg(self, recipient, body):
        # envío de un mensaje a un usuario específico (comunicación 1 a 1)
        message = self.Message()
        message['to'] = recipient
        message['type'] = 'chat'
        message['body'] = body

        print("Enviando mensaje '%s' a %s" % (body, recipient))
        message.send() # envío de stanza

    def receive_message(self, message):
        # recepción de mensaje enviado por algún usuario a mi directamente o por alguien en eun chat grupal 
        if message['type'] in ('chat', 'normal'):
            from_account = "%s@%s" % (message['from'].user, message['from'].domain)
            print("NOTIFICACION: Mensaje recibido! '%s' de %s" % (message["body"], from_account))
        elif message['type'] == 'groupchat':
            from_group = message["from"].user
            from_account = message["from"].resource
            print("NOTIFICACION: Mensaje recibido! %s @ %s : %s " % (from_account, from_group, message["body"]))

    """
                                    ------------------      Métodos de manejo de contactos. -------------------
    """
    def add_contact(self, contact_username):
        # agregar a un usuario a mi lista de contactos
        self.send_presence_subscription(contact_username)

    def get_my_contacts(self):
        # display a todos mis contactos
        # se obtiene toda la información de mis contactos del client_roster (o de mi diccionario de contactos)
        contacts_state = [
            "Username: {}, Estado: {}".format(username, self.my_contacts[username]["state"]) if not self.my_contacts[username]["status_msg"] \
                else "Username: {}, Estado: {}, Mensaje: {}".format(username, self.my_contacts[username]["state"], self.my_contacts[username]["status_msg"])\
                    for username in self.my_contacts.keys()
        ]
        # formulación de string que se devolverá al main para ser desplegado ahí
        to_str = '\n'
        for i in range(len(contacts_state)):
            to_str += "\t"+str(i+1)+". "+contacts_state[i]+"\n"
        to_str += '\n'
        return to_str
        
    
    def contact_sign_out(self, event):
        # recepción de notificación cuando un usuario se desconecta
        # se actualiza mi lista de contactos con el estado de 'offline'
        contact = JID(event['from']).bare
        if contact in self.my_contacts.keys(): # se hace esto porque los eventos presence_unavailable también pueden venir del server
            self.my_contacts[contact]['state'] = "Offline"
            print("NOTIFICACION: {} se ha desconectado.".format(contact))
        
    def contact_sign_in(self, event):
        # recepción de notificación cuando uno de mis contactos inicia sesión
        # se actualiza mi lista de contactos con el estado de 'online'
        if event['from'].domain != "conference.redes2020.xyz" and event['from'] != self.instance_name: # si el presence no viene de un group chat 
            try:
                self.my_contacts[JID(event['from']).bare]['state'] = "Online" 
                self.my_contacts[JID(event['from']).bare]['fulljid'] = event["from"] 
                self.my_contacts[JID(event['from']).bare]['status_msg'] = ''
            except KeyError:
                self.my_contacts[JID(event['from']).bare] = {'state': 'Online', 'fulljid': event['from'], 'status_msg': ''}
            print("NOTIFICACION: {} se ha conectado.".format(JID(event['from']).bare))

    def get_all_users(self):
        # envío de request para obtener a todos los usuarios registrados en el servidor
        users = ""
        iq = self.make_iq(
            id="get_all_registered_users", ito="search.redes2020.xyz")
        
        # stanza para query sobre todos los parámetros (Username, email, name) para encontrar a todos los usuarios
        get_users_form = ET.fromstring('\
            <query xmlns="jabber:iq:search">\
                <x xmlns="jabber:x:data" type="form">\
                    <field var="FORM_TYPE" type="hidden">\
                        <value>jabber:iq:search</value>\
                    </field>\
                    <field var="Username">\
                        <value>1</value>\
                    </field>\
                    <field var="Email">\
                        <value>1</value>\
                    </field>\
                    <field var="Name">\
                        <value>1</value>\
                    </field>\
                    <field var="search">\
                        <value>*</value>\
                    </field>\
                </x>\
            </query>\
        ')
        request = self.make_iq_set(iq = iq, sub=get_users_form)
        try:
            response = request.send(now=True) # se espera a que el servidor responda con todos los clientes registrados
            users = self.parse_users_response(response) # se hace un parse para que se impriman bonito
            return users
        except IqError as e:
            print("Query failed.", e)
        except IqTimeout:
            raise Exception("Unable to reach server.")
        
    def get_user_info(self, search, username, email, name):
        # encontrar a un usuario específico (y su información correspondiente) basado en un argumento (search) y parámetros de búsqueda
        iq = self.make_iq(
            id="get_one_user_info", ito="search.redes2020.xyz")
        query_str = '\
            <query xmlns="jabber:iq:search">\
                <x xmlns="jabber:x:data" type="form">\
                    <field var="FORM_TYPE" type="hidden">\
                        <value>jabber:iq:search</value>\
                    </field>'
        if username: # se agrega Username a los parámetros de búsqueda del stanza si el usuario lo desea
            query_str += '<field var="Username">\
                                <value>1</value>\
                        </field>'
        if email:# se agrega email a los parámetros de búsqueda del stanza si el usuario lo desea
            query_str += '<field var="Email">\
                                <value>1</value>\
                        </field>'
        if name: # se agrega el nombre a los parámetros de búsqueda del stanza si el usuario lo desea
            query_str += '<field var="Name">\
                                <value>1</value>\
                        </field>'
        query_str += '<field var="search">\
                        <value>{}</value>\
                    </field>\
                </x>\
            </query>\
        '.format(search)
        get_users_form = ET.fromstring(query_str)
        request = self.make_iq_set(iq = iq, sub=get_users_form)
        try:
            response = request.send(now=True) # esperar a que el servidor responda con algún usuario (de lo contrario se despliega que no se encontró ninguno)
            return self.parse_users_response(response)
        except IqError as e:
            print("Query failed.", e)
        except IqTimeout:
            raise Exception("Unable to reach server.")

    def parse_users_response(self, response):
        # un parse de la stanza resultante con todos los usuarios registrados en el servidor 
        # para devolver un print entendible y bonito 
        users_str = ""
        user_count = 1
        user_items = response.find('.//{jabber:x:data}x').findall(".//{jabber:x:data}item")
        for item in user_items:
            users_str += "\t" + str(user_count) + ". "
            fields = item.findall(".//{jabber:x:data}field")
            for field in fields:
                field_value = field.getchildren()[0].text
                if field_value: # si el field tiene valor alguno, que se agregue al print
                    users_str += "{}: {}\t".format(field.attrib["var"], field_value)
            users_str += "\n"
            user_count += 1
        return users_str
    
    """
                                    ------------------      Métodos de chat rooms o grupos. -------------------
    """
    def send_msg_to_room(self, room, msg):
        # enviar un mensaje a un chat grupal
        try:
            if room not in self.plugin['xep_0045'].getJoinedRooms(): # si el usuario no se ha unido al chat (a cada inicio de sesión debe hacerse)
                self.join_group(room) # se hace el join room 
            self.send_message(mto=room, mbody=msg, mtype='groupchat') # se envía el mensaje al chat 
        except:
            print("ERROR: No se ha podido parsear ese nombre de grupo.")
        # print("Joined rooms:", self.plugin['xep_0045'].getJoinedRooms())
    
    def join_group(self, room, nickname=None):
        # unirse a un chat grupal o crearlo si no existe
        try:
            if not nickname:
                nickname = self.instance_name.split("@")[0]
            status = self.my_contacts[self.instance_name]['status_msg']
            self.plugin['xep_0045'].joinMUC(room, nickname, wait=True, pstatus=status if status else None)
            if room not in self.plugin['xep_0045'].getJoinedRooms():
                print("Failed to join room.")
                return
            print("Chats grupales registrados:", ", ".join(list(self.plugin['xep_0045'].getJoinedRooms()))) # se hace display de los grupos a los cuales se ha registrado este usuario
            # NOTA: por alguna razón, aunque el server tire error de ingreso al room y el usuario no esté dentro, el plugin registra el room como que si hubiera ingresado sin problema
            # por tanto, la manera en la cual se puede saber si de verdad se ingresó al room, es esperar las notificaciones de '<este username> ha ingresado al chat.'
        except sleekxmpp.jid.InvalidJID: # en caso el nombre ingresado del room es inválido (por ejemplo, si tiene espacios o tildes)
            print("ERROR: No se ha podido parsear ese nombre de grupo.")

    def groupchat_notif(self, event):
        # recepción de evento en el cual un usuario ha ingresado a un chat al que ya estamos registrados. 
        new_usr = JID(event['from']).resource
        status = event['status']
        group = JID(event['from']).user
        notice = "NOTIFICACION: {} ha ingresado al chat de {}.".format(new_usr, group)
        notice = notice + " Mensaje de presencia: {}".format(status) if status else notice # hay casos en los que este evento trae un mensaje de presencia custom, por lo que se muestra si es que hay alguno
        print(notice)

    """
                                 ------------------      Métodos de manejo de envío de archivos. -------------------
    """

    def send_file_request(self, filename, recipient, mime_type="image/png", size=1024, description = 'Descripción genérica de una imagen a transferir.', file_date = None):
        # se envía el request de negociación acorde al SI File transfer protocol. 
        try: 
            r_fulljid = self.my_contacts[recipient]["fulljid"] # se busca dentro de mis contactos el fulljid del usuario ingresado (se necesita el full para este protocolo)
            if r_fulljid:
                response = self.plugin['xep_0096'].request_file_transfer( # se envía el request y se espera el response (se asume que responderá un .accept())
                    r_fulljid, 
                    name=filename, 
                    size=size, 
                    sid="ibb_file_transfer",
                    desc= description, 
                    date=file_date, 
                    mime_type=mime_type)
                
                try:
                    metodo = response['si']['feature_neg']['form']['field']['value']
                    print("INFO: Recipiente ha aceptado la solicitud de transferencia de archivos. Método:", metodo) # se hace un display del método escogido para la transferencia de archivos
                    self.send_file(filename, r_fulljid, mime_type) # se hace el envío. 
                except:
                    print("ERROR: no se pudo realizar la transferencia de archivos.")
            else:
                print("El usuario ingresado no está conectado.") # para hacer la negociación, es necesario que el usuario esté activo. 
        except KeyError:
            print("El usuario ingresado no está agregado a la lista de contactos.") # para obtener el fulljid es necesario que el usuario esté en mi lista de contactos
        except IqError as err:
            print("ERROR: ", err.iq['error']['text'])
        except IqTimeout:
            print("ERROR: Server took too long to respond.")

    
    def file_transfer_req(self, event):
        # se recibe una petición para el file transfer (para cuando se es receptor)
        self.files_recv.append({
            "file_name": event['si']['file']['name'],
            "mime_type": event['si']['mime_type'],
            "file_size": event['si']['file']['size'],
            "data": b""
        }) # se envía la data del archivo
        self.plugin['xep_0095'].accept(event['from'], event['si']['id']) # responder un accept para el request 
    
    def stream_opened(self, stream):
        # se abre un bytestream para el paso de archivos por chunks
        print('Stream abierto: %s from %s' % (stream.sid, stream.peer_jid))

    def stream_data(self, event):
        # se recibe los batches/chunks del archivo 
        # asumiendo que los archivos se enviarán en orden y entre parejas de clientes a la vez
        self.files_recv[len(self.files_recv)-1]['data'] += event['data'] # se agrega la data recibida a la que se recibió previamente

    def send_file(self, filename, receiver, mime_type):
        # al recibir el accept(), se comienza la transferencia del archivo. 
        stream = self.plugin['xep_0047'].open_stream(receiver) # se abre el stream 
        try:
            filename.split(".")[1] # se prueba si el archivo viene con extension
        except IndexError: # si tira error es porque el nombre del archivo no tenia extension
            filename = filename + '.' + mime_type.split("/")[1]
        with open(filename, 'rb') as f: # se abre el archivo en modo binary
            data = f.read()
            stream.sendall(base64.b64encode(data).decode('utf-8')) # se envía el archivo codificado en base64
        stream.close() # cuando finaliza se cierra el stream
        print("INFO: Archivo enviado!") # se notifica al usuario que se ha terminado de enviar el archivo. 

    def stream_end(self, event):
        try:
            # al obtener el evento, se consolida la informacion obtenida y se guarda en un archivo
            # solo funciona si es el receptor, pero este evento sucede en tanto receptor como emisor, por eso el try except
            file = self.files_recv.pop()
            file_data = base64.decodebytes(file['data']) 
            name_only = file["file_name"].split("/") # es posible que el nombre del archivo venga con el path absoluto o solo venga el nombre
            name_only = name_only[len(name_only) -1] # por lo que se procura de obtener unicamente el nombre del path
            try:
                name_only.split(".")[1] # se prueba si el archivo viene con extension
                filename = 'files_received/' + name_only
            except IndexError: # si tira error es porque el nombre del archivo no tenia extension
                filename = 'files_received/' + name_only + "." + file['mime_type'].split('/')[1]
            with open(filename, "wb") as fh:
                fh.write(file_data)
            print("INFO: Archivo recibido!") # se notifica al usuario que ha terminado de recibir el archivo, los archivos recibidos quedan en la carpeta files_received/
        except IndexError as err:
            # print("Index error:", err)
            pass
        
"""
                        ------------------      Métodos de creación de un cliente (o iniciación). -------------------
"""
def user_register(username, password):
    """ 
        User Register 
    """
    jid = xmpp.JID(username)
    xmpp_cli = xmpp.Client(jid.getDomain(), debug=['never'])
    xmpp_cli.connect()
    if xmpp.features.register(xmpp_cli,jid.getDomain(),{'username':jid.getNode(),'password':password}): # se utiliza el feature de xmpp para hacer el in-band registration
        print('El usuario se ha registrado exitosamente. \n')
    else:
        print('Ocurrió un error registrando al usuario.\n')

def user_login(username, password):

    """ 
        User sign in 
    """
    xmpp_client = Client(username, password)
    # esperar a que el cliente haya hecho log in correctamente 
    while xmpp_client.logged_in == -1:
        pass
    if xmpp_client.logged_in == 0:
        # autorizar que todos los users que quieran agregarme a sus contactos automaticamente lo hagan
        xmpp_client.auto_authorize = True
        return xmpp_client
     