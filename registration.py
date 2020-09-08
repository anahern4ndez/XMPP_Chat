import sleekxmpp

class RegistrableComponent :
 def __init__(self, jid, password, server, port, backend) :
    self.xmpp = sleekxmpp.componentxmpp.ComponentXMPP(jid, password, server, port)
    self.xmpp.add_event_handler("session_start", self.handleXMPPConnected)
    self.xmpp.add_event_handler("changed_subscription",
        self.handleXMPPPresenceSubscription)
    self.xmpp.add_event_handler("got_presence_probe",
        self.handleXMPPPresenceProbe)
    for event in ["message", "got_online", "got_offline", "changed_status"] :
        self.xmpp.add_event_handler(event, self.handleIncomingXMPPEvent)
    self.backend = backend
    self.backend.addMessageHandler(self.handleMessageAddedToBackend)
    self.xmpp.registerPlugin("xep_0030")
    self.xmpp.plugin["xep_0030"].add_feature("jabber:iq:register")
    self.xmpp.add_handler("<iq type='get' xmlns='jabber:client'>" +
    "<query xmlns='jabber:iq:register'/></iq>", self.handleRegistrationFormRequest)
    self.xmpp.add_handler("<iq type='set' xmlns='jabber:client'>" +
    "<query xmlns='jabber:iq:register'/></iq>", self.handleRegistrationRequest)
 def handleRegistrationFormRequest(self, request) :
    payload = ET.Element("{jabber:iq:register}query")
    payload.append(ET.Element("username"))
    payload.append(ET.Element("password"))
    self.sendRegistrationResponse(request, "result", payload)
 def handleRegistrationRequest(self, request) :
    jid = request.attrib["from"]
    user = request.find("{jabber:iq:register}query/{jabber:iq:register}username")
    password = request.find("{jabber:iq:register}query/{jabber:iq:register}password")
    if self.backend.registerXMPPUser(user, password, jid) :
       self.sendRegistrationResponse(request, "result")
    else :
        error = self.xmpp.makeStanzaError("forbidden", "auth")
        self.sendRegistrationResponse(request, "error", error)

def sendRegistrationResponse(self, request, type, payload = None) :
    iq = self.xmpp.makeIq(request.get("id"))
    iq.attrib["type"] = type
    iq.attrib["from"] = self.xmpp.fulljid
    iq.attrib["to"] = request.get("from")
    if payload :
        iq.append(payload)
        self.xmpp.send(iq)