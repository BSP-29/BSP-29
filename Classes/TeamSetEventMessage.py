from Classes.Packets.PiranhaMessage import PiranhaMessage


class TeamSetEventMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 14362
        self.messageVersion = 0
        self.EventSlot = 0

    def encode(self, fields, player=None):
        # Questo è un messaggio client->server, lato server in genere non lo encodi
        # Se mai ti servirà lato server, potrai scrivere qui i due VInt.
        pass

    def decode(self):
        fields = {}

        # C#: base.Decode();
        super().decode(fields)

        # C#: Stream.ReadVInt();  // ignorato
        _unk = self.readVInt()

        # C#: EventSlot = Stream.ReadVInt();
        self.EventSlot = self.readVInt()
        fields["EventSlot"] = self.EventSlot

        return fields

    def execute(message, calling_instance, fields, cryptoInit):
        # qui gestisci il cambio evento/mappa da parte del client
        player = calling_instance.player
        event_slot = fields.get("EventSlot", 1)

        # es: mappare event_slot -> SelectedMap, aggiornare Team, ecc.
        # player.SelectedMap = <mappa associata a event_slot>
        # e poi mandare TeamMessage/TeamSetEvent ai membri, se serve
        pass

    def getMessageType(self):
        return 14362

    def getMessageVersion(self):
        return self.messageVersion