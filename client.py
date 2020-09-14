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


class Client(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.logged_in = -1
        self.instance_name = jid
        self.latest_roster_version = -1
        self.my_contacts = {}

        self.add_event_handler("session_start", self.session_start, threaded=False, disposable=True)
        self.add_event_handler("message", self.receive_message, threaded=True, disposable=False)
        self.add_event_handler("failed_auth", self.on_failed_auth)
        self.add_event_handler("auth_success", self.on_auth_success)
        self.add_event_handler("got_offline", self.contact_sign_out)
        self.add_event_handler("presence_unavailable", self.contact_sign_out)
        self.add_event_handler("got_online", self.contact_sign_in)
        self.add_event_handler("groupchat_message", self.receive_message)
        # self.add_event_handler("presence_subscribed", self.added_contact) # server envia mensaje de add contact success
        # self.add_event_handler("presence_subscribe", self.on_auth_success)
        
        # If you wanted more functionality, here's how to register plugins:
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0199') # XMPP Ping
        self.register_plugin('xep_0050')
        self.register_plugin('xep_0133')
        self.register_plugin('xep_0045') # MUC


        # If you are working with an OpenFire server, you will
        # need to use a different SSL version:
        self.ssl_version = ssl.PROTOCOL_TLS

        if self.connect():
            print("Opened XMPP Connection")
            self.process(block=False)
        else:
            raise Exception("Unable to connect to server.")

    def session_start(self, event):
        try:
            self.send_presence()
            self.get_roster(block = True, timeout = 3)
            # parse del roster para obtener estado de los contactos 
            for contact in self.client_roster.keys():
                self.my_contacts[JID(contact).bare] = "Offline"

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
        elif message['type'] == "image":
            received = message['body'].encode('utf-8')
            received = base64.decodebytes(received)
            with open("received_img.png", "wb") as fh:
                fh.write(received)


    def add_contact(self, contact_username):
        self.send_presence_subscription(contact_username)

    def get_my_contacts(self):
        contacts_state = ["Username: {}, Estado: {}".format(username, state) for username,state in self.my_contacts.items()]
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
            self.my_contacts[contact] = "Offline"
        
    def contact_sign_in(self, event):
        self.my_contacts[JID(event['from']).bare] = "Online"

    def on_failed_auth(self, event):
        print("auth fail event", event)
        self.logged_in = 1

    def on_auth_success(self, event):
        self.logged_in = 0
    
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
        try:
            response = self.send_message(mto=room, mbody=msg, mtype='groupchat')
            print("send msg response", response)
        except XMPPError:
            self.join_group(room)
            self.send_message(mto=room, mbody=msg, mtype='groupchat')
    
    def join_group(self, room, nickname=None):
        if not nickname:
            nickname = self.instance_name.split("@")[0]
        self.plugin['xep_0045'].joinMUC(room, nickname, wait=True)
        # self.plugin['xep_0045'].setAffiliation(room,nickname,affiliation='owner')
    
    def send_file(self, filename, recipient):
        message = ''
        with open(filename, "rb") as img_file:
            message = base64.b64encode(img_file.read()).decode('utf-8')
        self.send_message(mto=recipient,mbody=message,mtype="chat")

def user_register(username, password):
    """ 
        User Register 
    """
    jid = xmpp.JID(username)
    xmpp_cli = xmpp.Client(jid.getDomain())
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
     