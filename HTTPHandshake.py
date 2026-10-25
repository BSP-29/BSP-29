# packets/HTTPHandshake.py
import os
import struct
from Classes.Packets.PiranhaMessage import PiranhaMessage

class HTTPHandshake(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0
        self.news_html = self.load_news_html()
        self.fields = {}
        self.player = None
    
    def load_news_html(self):
        """Carica news.html dalla root"""
        try:
            with open('news.html', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>🐟 Piranha Brawl Server v29</title>
                <style>
                    body { background: #0a0a1a; color: white; font-family: Arial; text-align: center; padding: 50px; }
                    h1 { color: #e94560; }
                </style>
            </head>
            <body>
                <h1>🐟 Piranha Server</h1>
                <p>news.html non trovato nella root!</p>
                <p>Percorso: {}</p>
                <p>PacketID: 18245 - HTTP Handshake</p>
            </body>
            </html>
            """.format(os.getcwd())
    
    def encode(self, fields=None, player=None):
        """Codifica il pacchetto 18245 con la risposta HTTP"""
        
        # Salva fields e player se passati
        if fields is not None:
            self.fields = fields
        if player is not None:
            self.player = player
        
        # Costruisci la risposta HTTP completa
        html_content = self.news_html
        
        # Sostituisci variabili dinamiche se disponibili
        players_online = 0
        if self.player and hasattr(self.player, 'server') and hasattr(self.player.server, 'players'):
            players_online = len(self.player.server.players)
        elif hasattr(self, 'server') and hasattr(self.server, 'players'):
            players_online = len(self.server.players)
        
        html_content = html_content.replace("{players}", str(players_online))
        
        response = f"""HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: {len(html_content)}
Connection: keep-alive
Server: Piranha/v29
X-Powered-By: Piranha

{html_content}"""
        
        # Usa writeString invece di writeBytes (più semplice)
        self.writeString(response)
        
        print(f"[HTTPHandshake] Inviata risposta HTML ({len(response)} bytes)")
        return self
    
    def decode(self):
        """Decodifica la richiesta HTTP (se necessario)"""
        try:
            http_request = self.readString()
            print(f"[HTTPHandshake] Richiesta ricevuta: {http_request[:100]}...")
        except:
            print("[HTTPHandshake] Nessuna richiesta HTTP da decodificare")
        return {}
    
    def execute(self, calling_instance, fields):
        """Esegue il pacchetto (chiamato da MessageManager)"""
        print(f"[HTTPHandshake] Esecuzione pacchetto 18245")
        
        # Ottieni il player dalla connessione
        if hasattr(calling_instance, 'player'):
            self.player = calling_instance.player
        
        self.fields = fields or {}
        
        # Codifica e invia la risposta
        self.encode(self.fields, self.player)
        
        # Invia il pacchetto al client
        calling_instance.sendMessage(self)
    
    def getMessageType(self):
        return 18245
    
    def getMessageVersion(self):
        return self.messageVersion
    
    def isServerToClient(self):
        return True
    
    def isClientToServer(self):
        return False