from Classes.Commands.LogicCommand import LogicCommand
import binascii

class LogicGatchaCommand(LogicCommand):
    def __init__(self, commandData):
        super().__init__(commandData)
        # commandData in BSDS contiene spesso i byte grezzi del comando
        if isinstance(commandData, bytes):
            print(f"--- [GATCHA DEBUG] ---")
            print(f"PAYLOAD: {binascii.hexlify(commandData).decode('utf-8').upper()}")
            print(f"----------------------")
        
        self.box_type = "Unknown"
        self.rewards = []

    def decode(self, calling_instance):
        fields = {}
        # Leggiamo l'header per far avanzare lo stream del messaggio
        # ed evitare che il comando successivo legga dati sbagliati
        LogicCommand.decode(calling_instance, fields, False)
        
        # Se il crash persiste, dobbiamo leggere almeno un VInt per "pulire" lo stream
        try:
            fields["Unk"] = calling_instance.readVInt()
        except:
            pass
            
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        pass

    def getCommandType(self):
        return 500