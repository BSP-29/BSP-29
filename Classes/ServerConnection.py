import socket

import Configuration
from Classes.BanManager import BanManagerInstance
from Classes.Connection import Connection
from Classes.Messaging import Messaging


class ServerConnection:
    def __init__(self, address):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if Configuration.settings["DisableNagle"] == True:
            self.server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        self.setupConnection(address)

    def setupConnection(self, address):
        self.server.bind(address)
        print("Listening for new connection...")
        while True:
            self.server.listen()
            client_socket, client_address = self.server.accept()
            client_ip = client_address[0]
            
            # Controlla se l'IP è bannato
            ip_ban = BanManagerInstance.is_ip_banned(client_ip)
            if ip_ban:
                print(f"[BAN] Connessione rifiutata da IP bannato: {client_ip} - Motivo: {ip_ban['reason']}")
                # Invia messaggio di ban invece di chiudere subito
                try:
                    ban_reason = ip_ban.get('reason', '')
                    if not ban_reason:
                        ban_reason = "You got Banned"
                    Messaging.sendMessage(20103, {
                        "Socket": client_socket,
                        "ErrorID": 11,  # Ban error code
                        "FingerprintData": "{}",
                        "ContentURL": "",
                        "Message": ban_reason
                    }, None)  # cryptoInit sarà None per nuove connessioni
                except Exception as e:
                    print(f"[BAN] Errore invio messaggio ban: {e}")
                try:
                    client_socket.close()
                except Exception:
                    pass
                continue
            
            print("New connection with address", client_ip, "on port", client_address[1])
            Connection(client_socket, client_address).start()
