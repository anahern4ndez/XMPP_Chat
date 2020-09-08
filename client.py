import logging
import xmpp, sys
import sleekxmpp
from sleekxmpp.exceptions import IqError, IqTimeout
import ssl
import xml.etree.ElementTree as ET


class Client(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)


        self.instance_name = jid

        self.add_event_handler("session_start", self.session_start, threaded=False, disposable=True)
        self.add_event_handler("message", self.receive_message, threaded=True, disposable=False)

        # If you wanted more functionality, here's how to register plugins:
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0199') # XMPP Ping
        self.register_plugin('xep_0077') # in band registration

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
        # print("***** SESSION STARTED *****")
        self.send_presence()
        print(self.get_roster())

        # Most get_*/set_* methods from plugins use Iq stanzas, which
        # can generate IqError and IqTimeout exceptions
        
        # try:
        #     self.get_roster()
        # except IqError as err:
        #     logging.error('There was an error getting the roster')
        #     logging.error(err.iq['error']['condition'])
        #     self.disconnect()
        # except IqTimeout:
        #     logging.error('Server is taking too long to respond')
        #     self.disconnect()

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
            # print("XMPP Message: %s" % message)
            from_account = "%s@%s" % (message['from'].user, message['from'].domain)
            print("Message received '%s' from %s" % (message["body"], from_account))

            # if self.instance_name in message['body'].lower():
            #     print("Caught test message: %s" % message)
            #     # message.reply("%s was listening!" % self.instance_name).send()
            # else:
            #     print("Uncaught command from %s: %s" % (from_account, message['body']))

    def disconnect_user(self):
        # Using wait=True ensures that the send queue will be
        # emptied before ending the session.
        print("Disconnecting. Waiting for send queue to empty...")
        self.disconnect(wait=True)

    # def sendMessage(self, recipient, msg):
    #     self.send_message(mto=recipient,
    #                       mbody=msg,
    #                       mtype='chat')
    def delete_user(self):
        # self.Remove()
        # delete_req = self.Iq()
        # delete_req["type"] = 'set'
        # delete_req["from"] = self.instance_name
        # delete_req["register"] = ''
        # # delete_req["register"]["unregistered_user"] = ''
        # try:
        #     delete_req.send(now=True)
        #     print("User successfully deleted")
        # except IqError:
        #     raise Exception("Deleting failed.")
        # except IqTimeout:
        #     raise Exception("Unable to reach server.")
        remov_obj = ET.fromstring(
            "<query xmlns='jabber:iq:register'>\
                <remove/>\
            </query>")
        delete_req = self.make_iq_set(sub=remov_obj)
        # delete_req["id"] = "delete_user"
        print("\ndelete req", delete_req, "\n")
        try:
            delete_req.send(now=True)
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
    # username = "anah@redes2020.xyz"
    # password = "hola"
    jid = xmpp.JID(username)
    xmpp_cli = xmpp.Client(jid.getDomain())
    xmpp_cli.connect()
    if xmpp.features.register(xmpp_cli,jid.getDomain(),{'username':jid.getNode(),'password':password}):
        sys.stderr.write('Success\n')
        sys.exit(0)
    else:
        sys.stderr.write('Error\n')
        sys.exit(1)

def user_login(username, password):

    """ 
        User sign in 
    """
    # # Ideally use optparse or argparse to get JID,
    # # password, and log level.

    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    
    username = input("Ingrese el nombre de usuario: ")
    password = input("Ingrese la password: ")
    # # xmpp = Client(username+'@redes2020.xyz', password)
    # username = "ana"
    # password = "hola")
    xmpp_cli = Client(username+'@redes2020.xyz', password)

    # msg = input("ingrese mensaje a enviar: ")
    # recipient = input("ingrese username del recipiente: ")
    # xmpp_cli.send_msg(recipient+'@redes2020.xyz', msg)
    
    # Using wait=True ensures that the send queue will be
    # emptied before ending the session.
    # xmpp_cli.delete_user()
    # xmpp_cli.disconnect_user()
    return xmpp_cli