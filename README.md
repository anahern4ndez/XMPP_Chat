# XMPP_Chat
 
 
## Description

This project consists in the implementation of a multi-user chat using the XMPP protocol. Functionalities included:
 1. Sending a DM to someone
 2. Display all existing users (registered in the server)
 3. Display all my contacts
 4. Add someone to my contacts                    
 5. Search and show for someone's details/info
 6. Create/join a room
 7. Send message to a room
 8. Define presence message
 9. Send a file
 10. Send notifications
 11. Delete user                  
 12. Log out
 13. Sign up
 14. Sign in

These functionalities will be further explained in the following sections.

## First steps

### Requirements

This project needs previous installation of python>=3.8 y pip>=20.2.2. Aditionally, the libraries for the implementation of XMPP are also needed, these dependencies can be easily installed running: `pip install -r requirements.txt` in your console/terminal. A **very** important aspect is that the following libraries **must** have the following versions:
1. sleexmpp=1.3.1
2. pyasn1==0.3.7
3. pyasn1-modules==0.1.5

### Instalación

1. Clone this repository using `git clone https://github.com/her17138/XMPP_Chat.git`
2. Run `pip install -r requirements.txt` to install all necessary libraries. Should any error with tkinter appear, run `pip install tkinter`.
3. Run `python3 main.py` to start the implementation of the client using XMPP.

## Project structure

### Folders

The `files_received` folder is where all the files received from other users will be stored. 

### Files
#### main.py

This file contains the main menu shown to the user, contains displays and inputs for then calling the functions described in `client.py`.

#### client.py

Contains the actual implementation of the client, the Client class has all the methods and attributes necessary for is correct functioning, except for the two functions for signing up (this was done with xmpppy package, not sleekxmpp) and for logging in. Up next is the more thorough explanation of the implemented features. 

##### 1. Sending a DM to someone

To send a direct message, the user enters only the user part of the JID (without the domain, this is added automatically after) and then enters the message. It can be sent to any user, whether it's in the client's contact list or not. 

##### 2. Display all existing users (registered in the server)

A search is done looking for all the users registered in the server and all their available information is returned and displayed (username, JID, email - if any - and name - if any). 

##### 3. Display all my contacts

A search is done within the client's roster for all the users that have a 'subscription = both' relationship with the client. Their bare JID, status and presence message - if any - is returned and displayed. 

##### 4. Add someone to my contacts                    

By default, this client has the property of automatically accepting all incoming 'friendship requests', so a prompt isn't necessary for this. The username (JID without domain) is all that needs to be entered. 

##### 5. Search and show for someone's details/info

The user is given the options of which search parameters he/she wishes and the term to search with. By default, all search parameters (Username/Name/Email) are taken into consideration (the client search for the term in all three parameters).

##### 6. Create/join a room

The user enters the name of the group it wishes to join (without the domain) and then a request to the server is made. If the room does not exist, it'll be created. To know if the user successfully joined the room, a notification must appear with '<this client username> ha ingresado al chat.' Otherwise it is assumed that an error ocurred and the user couldn't join the room (this error will not be displayed). In this case, the user can retry to join with a different nickname. When testing with certain usernames, it's username proved to be a problem when joining rooms a small amount of times. 

##### 7. Send message to a room

The best route of action for this feature is to first join the room (with feature 6) and then sending the message. However, this client will check if the user has already joined the room or not, in which case it will send a request to the server to join and after receiving the OK response from the server, the message will be sent. 

##### 8. Define presence message

The presence message was defined as the "state" message of a user (similar to custom states in popular messaging apps like WhatsApp). These are not persistent in the server so each time `main.py` reruns, previously set presence messages are deleted. When a contact redefines (or customizes) its presence message, this client receives the Presence stanza and a notification is activated informing which client has changed its presence and the actual message. This presence, as long as the session is open, is stored in the client's attributes and all contact's presences can be displayed (if they have any) with the feature #3 (contacts that haven't redefined their presences, will not be shown one).

##### 9. Send a file

First the user is asked for the receiver of the file, then the file explorer is opened (with help of the tkinter package) where the user can choose the file it wants to send. It is recommended that the file to be sent be of csv, pdf, jpg, jpeg, png or txt type; all other formats have not been tested and support is not assured. 

The xep_0096 and xep_0095 plugins are used to start the file transfer negotiation, when the .accept() of the other user is received, a bytestream is opened, through which chunks or batches of the files are sent. Even though in the negotiation the SOCKS5 and IBB protocol are set as options, only the IBB protocol is implemented, therefor both the sender and the receiver must have - at least - this protocol implemented. 

As default, it is set that the client will automatically accept all file transfer requests (negotiation .offer()), so a prompt to accept a request is not necessary. 

##### 10. Send notifications

Notifications are displayed with prints with the prefix *NOTIFICACION*, the client makes said notifications for the following events:
- When a contact signs in. 
- When a contact logs out. 
- When a contact redefines its custom presence message. 
- When someone enters the room (groupchat) the client is in. 
- When someone sends a message in the room (groupchat) the client is in. 
- When someone sends the client a direct message.  


##### 11. Delete user                  

If the user wants to, this client can be deleted or unregistered from the server. After selecting this option, the user is sent back to the first menu and has to log in again (with other credentials or create another user).

##### 12. Log out

User is disconnected. It is then sent back to the first menu to log in again, register another user or exit the program. 

##### 13. Sign up

For this case it is assumed that the credentials (username, password) used for the new client does not exist in the server. The xmpppy package is used to register the new client/user. 

##### 14. Sign in

When a user wishes to sign/log in, after entering its credentials, it is made known to the user (through a print) that their data is being verified. When an auth_success is received, the user is logged in correctly and is then shown the main menu containing the options to execute features #1-9 and #11-12. Otherwise - in the case of an auth_fail, the user has not logged in correctly, access is denied and has to sign in again. 

Should any of the following errores appear when an incorrect sign in is done:
- ERROR    No appropriate login method.
- ERROR    Error reading from XML stream.

No need to worry, these errores don't affect the client's run. However if its proving to be troublesome, exit the program and run it again and log in with the correct credentials. Be noted that when these errors appear, in a few tests it showed to keep other features from functioning correctly (it appeared to happen randomly), so it is recommended to exit and rerun the program if an incorrect sign in is made. 

## Features
- 🐍 Python — Programming language used. 
- 📬 XMPP  — Message exchange protocol.


