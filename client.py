import logging
import xmpp, sys
import sleekxmpp
from sleekxmpp.exceptions import IqError, IqTimeout
from OpenSSL import SSL


class Client(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)

        # If you wanted more functionality, here's how to register plugins:
        # self.register_plugin('xep_0030') # Service Discovery
        # self.register_plugin('xep_0199') # XMPP Ping

        # Here's how to access plugins once you've registered them:
        # self['xep_0030'].add_feature('echo_demo')

        # If you are working with an OpenFire server, you will
        # need to use a different SSL version:
        import ssl
        # self.ssl_version = ssl.PROTOCOL_SSLv23
        self.ssl_version = ssl.PROTOCOL_TLS

    def session_start(self, event):
        self.send_presence()
        # self.get_roster()

        # Most get_*/set_* methods from plugins use Iq stanzas, which
        # can generate IqError and IqTimeout exceptions
        #
        try:
            self.get_roster()
        except IqError as err:
            logging.error('There was an error getting the roster')
            logging.error(err.iq['error']['condition'])
            self.disconnect()
        except IqTimeout:
            logging.error('Server is taking too long to respond')
            self.disconnect()

    def message(self, recipient, msg):
        # if msg['type'] in ('chat', 'normal'):
        #     msg.reply("Thanks for sending\n%(body)s" % msg).send()
        self.send_message(mto=self.recipient + "@redes2020.xzy",
                          mbody=self.msg,
                          mtype='chat')


if __name__ == '__main__':
    """ 
        User Register 
    """
    # username = "ana@redes2020.xyz"
    # password = "hola"
    # jid = xmpp.JID(username)
    # xmpp_cli = xmpp.Client(jid.getDomain())
    # xmpp_cli.connect()
    # if xmpp.features.register(xmpp_cli,jid.getDomain(),{'username':jid.getNode(),'password':password}):
    #     sys.stderr.write('Success\n')
    #     sys.exit(0)
    # else:
    #     sys.stderr.write('Error\n')
    #     sys.exit(1)

    """ 
        User sign in 
    """
    # Ideally use optparse or argparse to get JID,
    # password, and log level.

    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    # username = input("Ingrese el nombre de usuario: ")
    # password = input("Ingrese la password: ")
    # xmpp = Client(username+'@redes2020.xyz', password)
    username = "ana"
    password = "hola"
    xmpp_cli = Client(username+'@redes2020.xyz', password)
    xmpp_cli.connect()
    xmpp_cli.process(block=True)

    msg = input("ingrese mensaje a enviar: ")
    recipient = input("ingrese username del recipiente: ")
    xmpp_cli.send_message(recipient, msg)