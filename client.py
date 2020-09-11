import logging
import xmpp, sys
import sleekxmpp
from sleekxmpp.exceptions import IqError, IqTimeout
from sleekxmpp.xmlstream import XMLStream, JID
import ssl
import xml.etree.ElementTree as ET



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
        # self.add_event_handler("presence_subscribed", self.added_contact) # server envia mensaje de add contact success
        # self.add_event_handler("presence_subscribe", self.on_auth_success)
        
        # If you wanted more functionality, here's how to register plugins:
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0199') # XMPP Ping
        self.register_plugin('xep_0077') # in band registration
        self.register_plugin('xep_0050')
        self.register_plugin('xep_0133')

        # Here's how to access plugins once you've registered them:
        # self['xep_0030'].add_feature('echo_demo')

        # If you are working with an OpenFire server, you will
        # need to use a different SSL version:
        # self.ssl_version = ssl.PROTOCOL_SSLv23
        self.ssl_version = ssl.PROTOCOL_TLS
        if self.connect():
            print("Opened XMPP Connection")
            self.process(block=False)
        else:
            raise Exception("Unable to connect to server.")

    def session_start(self, event):
        # print(self.get_roster())

        # Most get_*/set_* methods from plugins use Iq stanzas, which
        # can generate IqError and IqTimeout exceptions
        
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

        # self.sendMessage(self.recipient, self.msg)

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

            # if self.instance_name in message['body'].lower():
            #     print("Caught test message: %s" % message)
            #     # message.reply("%s was listening!" % self.instance_name).send()
            # else:
            #     print("Uncaught command from %s: %s" % (from_account, message['body']))
    def add_contact(self, contact_username):
        self.send_presence_subscription(contact_username)
        # print("subs stanza", JID(contact_username).bare)
        # self.update_roster(JID(contact_username).bare, subscription='both')

    def get_my_contacts(self):
        # self.send_presence()
        # my_roster = self.get_roster(block = True, timeout = 3)
        # print("roster contacts", self.client_roster)
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
        print("all users on server",self['xep_0030'].get_info('search.redes2020.xyz'))
        # # print("get commands", self['xep_0133'].get_commands('redes2020.xyz'))
        # print("2all users on server",self['xep_0050'].send_command('search.redes2020.xyz', 'http://jabber.org/protocol/admin#get_registered_users_list'))
        request = self.make_iq(id="get_all_registered_users", itype="get", iquery="jabber:iq:search")
        print(request)
        try:
            request.send(now=True)
            print("User successfully deleted")
        except IqError as e:
            print("Deleting failed.", e)
            # raise Exception("Deleting failed.")
        except IqTimeout:
            raise Exception("Unable to reach server.")

def user_register(username, password):
    """ 
        User Register 
    """
    jid = xmpp.JID(username)
    xmpp_cli = xmpp.Client(jid.getDomain())
    xmpp_cli.connect()
    if xmpp.features.register(xmpp_cli,jid.getDomain(),{'username':jid.getNode(),'password':password}):
        print('Successfully registered new user. \n')
        # sys.exit(0)
    else:
        print('Error registering user.\n')
        # sys.exit(1)

def user_login(username, password):

    """ 
        User sign in 
    """
    xmpp_client = Client(username, password)
    # do while
    # await ??
    while xmpp_client.logged_in == -1:
        pass
    if xmpp_client.logged_in == 0:
        # autorizar que todos los users que quieran agregarme a sus contactos automaticamente lo hagan
        xmpp_client.auto_authorize = True
        return xmpp_client
     