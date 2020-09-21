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
        self.instance_name = JID(jid).bare
        self.latest_roster_version = -1
        self.my_contacts = {}
        self.contacts_jids = []
        self.files_recv = []

        self.add_event_handler("session_start", self.session_start, threaded=False, disposable=True)
        self.add_event_handler("message", self.receive_message, threaded=True, disposable=False)
        self.add_event_handler("failed_auth", self.on_failed_auth)
        # self.add_event_handler("auth_success", self.on_auth_success)
        self.add_event_handler("got_offline", self.contact_sign_out)
        self.add_event_handler("presence_unavailable", self.contact_sign_out)
        self.add_event_handler("got_online", self.contact_sign_in)
        # self.add_event_handler("groupchat_message", self.receive_message)
        self.add_event_handler("roster_update", self.roster_update)
        self.add_event_handler("changed_status", self.changed_status)
        self.add_event_handler("si_request", self.file_transfer_req)
        # self.add_event_handler("presence_subscribed", self.added_contact) # server envia mensaje de add contact success
        # self.add_event_handler("presence_subscribe", self.on_auth_success)
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
    
    def roster_update(self, event):
        # print("contacts in client roster", self.client_roster)
        # se agrega un usuario que no estaba en mis contactos
        for contact in self.client_roster.keys():
            contactjid = JID(contact)
            if (contactjid.bare not in self.my_contacts.keys()) and (contactjid.domain != "conference.redes2020.xyz"):
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
            self.send_presence()
            self.get_roster(block = True, timeout = 5)
            # parse del roster para obtener estado de los contactos 
            # print("contacts in client roster", self.client_roster)
            for contact in self.client_roster.keys():
                self.my_contacts[JID(contact).bare] = {'state': "Offline", 'fulljid': "", 'status_msg': ''}
            # print("Joined rooms:", ", ".join(list(self.plugin['xep_0045'].getJoinedRooms())))
            self.logged_in = 0
            

        except IqError as err:
            logging.error('There was an error getting the roster')
            logging.error(err.iq['error']['condition'])
            self.disconnect()
        except IqTimeout:
            logging.error('Server is taking too long to respond')
            self.disconnect()

    def send_msg(self, recipient, body):
        message = self.Message()
        message['to'] = recipient
        message['type'] = 'chat'
        message['body'] = body

        print("Sending message '%s' to %s" % (body, recipient))
        message.send()

    def receive_message(self, message):
        if message['type'] in ('chat', 'normal'):
            from_account = "%s@%s" % (message['from'].user, message['from'].domain)
            print("Message received '%s' from %s" % (message["body"], from_account))
        elif message['type'] == 'groupchat':
            from_group = message["from"].user
            from_account = message["from"].resource
            print("Message received! %s @ %s : %s " % (from_account, from_group, message["body"]))

    def add_contact(self, contact_username):
        self.send_presence_subscription(contact_username)

    def get_my_contacts(self):
        contacts_state = [
            "Username: {}, Estado: {}".format(username, self.my_contacts[username]["state"]) if not self.my_contacts[username]["status_msg"] \
                else "Username: {}, Estado: {}, Mensaje: {}".format(username, self.my_contacts[username]["state"], self.my_contacts[username]["status_msg"])\
                    for username in self.my_contacts.keys()
        ]
        to_str = '\n'
        for i in range(len(contacts_state)):
            to_str += "\t"+str(i+1)+". "+contacts_state[i]+"\n"
        to_str += '\n'
        return to_str
        
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
        delete_req = self.make_iq_set(sub=remov_obj)
        try:
            delete_req.send(now=True)
            print("User successfully deleted")
        except IqError as e:
            print("Deleting failed.", e)
            # raise Exception("Deleting failed.")
        except IqTimeout:
            raise Exception("Unable to reach server.")
    
    def contact_sign_out(self, event):
        contact = JID(event['from']).bare
        if contact in self.my_contacts.keys(): # se hace esto porque los eventos presence_unavailable también pueden venir del server
            self.my_contacts[contact]['state'] = "Offline"
            print("INFO: {} se ha desconectado.".format(contact))
        
    def contact_sign_in(self, event):
        # print("resource?", event['from'].user, "from", event['from'])
        if event['from'].domain != "conference.redes2020.xyz" and event['from'] != self.instance_name: # si el presence no viene de un group chat 
            try:
                self.my_contacts[JID(event['from']).bare]['state'] = "Online" 
                self.my_contacts[JID(event['from']).bare]['fulljid'] = event["from"] 
                self.my_contacts[JID(event['from']).bare]['status_msg'] = ''
            except KeyError:
                self.my_contacts[JID(event['from']).bare] = {'state': 'Online', 'fulljid': event['from'], 'status_msg': ''}
            print("INFO: {} se ha conectado.".format(JID(event['from']).bare))

    def on_failed_auth(self, event):
        print("auth fail event", event)
        self.logged_in = 1

    # def on_auth_success(self, event):
    #     # self.logged_in = 0
    
    def get_all_users(self):
        users = ""
        iq = self.make_iq(
            id="get_all_registered_users", ito="search.redes2020.xyz")
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
            response = request.send(now=True)
            users = self.parse_users_response(response)
            return users
        except IqError as e:
            print("Query failed.", e)
        except IqTimeout:
            raise Exception("Unable to reach server.")
        
    def get_user_info(self, search, username, email, name):
        iq = self.make_iq(
            id="get_one_user_info", ito="search.redes2020.xyz")
        query_str = '\
            <query xmlns="jabber:iq:search">\
                <x xmlns="jabber:x:data" type="form">\
                    <field var="FORM_TYPE" type="hidden">\
                        <value>jabber:iq:search</value>\
                    </field>'
        if username:
            query_str += '<field var="Username">\
                                <value>1</value>\
                        </field>'
        if email:
            query_str += '<field var="Email">\
                                <value>1</value>\
                        </field>'
        if name:
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
            response = request.send(now=True)
            return self.parse_users_response(response)
        except IqError as e:
            print("Query failed.", e)
        except IqTimeout:
            raise Exception("Unable to reach server.")

    def parse_users_response(self, response):
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
    
    def send_msg_to_room(self, room, msg):
        if room not in self.plugin['xep_0045'].getJoinedRooms():
            self.join_group(room)
        self.send_message(mto=room, mbody=msg, mtype='groupchat')
        # print("Joined rooms:", self.plugin['xep_0045'].getJoinedRooms())
    
    def join_group(self, room, nickname=None):
        if not nickname:
            nickname = self.instance_name.split("@")[0]
        status = self.my_contacts[self.instance_name]['status_msg']
        self.plugin['xep_0045'].joinMUC(room, nickname, wait=True, pstatus=status if status else None)
        if room not in self.plugin['xep_0045'].getJoinedRooms():
            print("Failed to join room.")
            return
        print("Joined rooms:", ", ".join(list(self.plugin['xep_0045'].getJoinedRooms())))
    
    def send_file_request(self, filename, recipient, mime_type="image/png", size=1024, description = 'Descripción genérica de una imagen a transferir.', file_date = None):
        try: 
            r_fulljid = self.my_contacts[recipient]["fulljid"]
            if r_fulljid:
                response = self.plugin['xep_0096'].request_file_transfer(
                    r_fulljid, 
                    name=filename, 
                    size=size, 
                    sid="ibb_file_transfer",
                    desc= description, 
                    date=file_date, 
                    mime_type=mime_type)
                # print("client response to file transf", response)
                try:
                    metodo = response['si']['feature_neg']['form']['field']['value']
                    # print('response keys', response['si']['feature_neg']['form']['field']['option'].keys(), response['si']['feature_neg']['form']['field'].keys())
                    print("INFO: Recipiente ha aceptado la solicitud de transferencia de archivos. Método:", metodo)
                    self.send_file(filename, r_fulljid, mime_type)
                except:
                    print("ERROR: no se pudo realizar la transferencia de archivos.")
            else:
                print("El usuario ingresado no está conectado.")
        except KeyError:
            print("El usuario ingresado no está agregado a la lista de contactos.")
        except IqError as err:
            print("ERROR: ", err.iq['error']['text'])
        except IqTimeout:
            print("ERROR: Server took too long to respond.")

    
    def file_transfer_req(self, event):
        # print("file transf event", event)
        self.files_recv.append({
            "file_name": event['si']['file']['name'],
            "mime_type": event['si']['mime_type'],
            "file_size": event['si']['file']['size'],
            "data": b""
        })
        self.plugin['xep_0095'].accept(event['from'], event['si']['id']) # responder un accept para el request 
    
    def stream_opened(self, stream):
        print('Stream abierto: %s from %s' % (stream.sid, stream.peer_jid))

    def stream_data(self, event):
        # asumiendo que los archivos se enviarán en orden y entre parejas de clientes a la vez
        self.files_recv[len(self.files_recv)-1]['data'] += event['data']

    def send_file(self, filename, receiver, mime_type):
        stream = self.plugin['xep_0047'].open_stream(receiver)

        try:
            filename.split(".")[1] # se prueba si el archivo viene con extension
        except IndexError: # si tira error es porque el nombre del archivo no tenia extension
            filename = filename + '.' + mime_type.split("/")[1]
        with open(filename, 'rb') as f:
            data = f.read()
            stream.sendall(base64.b64encode(data).decode('utf-8'))
        stream.close()
        print("INFO: Archivo enviado!")

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
            print("INFO: Archivo recibido!")
        except IndexError as err:
            # print("Index error:", err)
            pass
        

    def update_presence(self, new_status):
        self.send_presence(
            pshow="chat",
            pstatus=new_status
        )
    def groupchat_notif(self, event):
        # print("groupchat presence data", event, event.keys())
        new_usr = JID(event['from']).resource
        status = event['status']
        group = JID(event['from']).user
        notice = "INFO: {} ha ingresado al chat de {}.".format(new_usr, group)
        notice = notice + " Mensaje de ingreso: {}".format(status) if status else notice
        print(notice)
        
    def changed_status(self, event):
        from_usr = JID(event['from'])
        if event['status'] and from_usr.domain != 'conference.redes2020.xyz': # si el mensaje de presencia trae un estado, realizar el cambio y la notificacion
            self.my_contacts[from_usr.bare]['status_msg'] = event['status']
            print("INFO: {} ha cambiado el mensaje de su estado a '{}'".format(from_usr.user, event['status']))

def user_register(username, password):
    """ 
        User Register 
    """
    jid = xmpp.JID(username)
    xmpp_cli = xmpp.Client(jid.getDomain(), debug=['never'])
    xmpp_cli.connect()
    if xmpp.features.register(xmpp_cli,jid.getDomain(),{'username':jid.getNode(),'password':password}):
        print('Successfully registered new user. \n')
    else:
        print('Error registering user.\n')

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
     