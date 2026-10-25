class ClientsManager:
    PlayersList = {}

    def AddPlayer(playerID, socket, session=None):
        if isinstance(playerID, list):
            playerID = playerID[-1]
        playerID = int(playerID)

        if playerID in ClientsManager.PlayersList:
            ClientsManager.RemovePlayer(playerID)
        
        client_data = {"Socket": socket}
        if session is not None:
            client_data["Session"] = session
        ClientsManager.PlayersList[playerID] = client_data

    def RemovePlayer(playerID):
        # Se playerID è una lista [0, 3], prendiamo l'ultimo elemento (3)
        if isinstance(playerID, list):
            playerID = playerID[-1]
            
        try:
            ClientsManager.PlayersList.pop(playerID)
        except KeyError:
            print(f"⚠️ Impossibile rimuovere: l'ID {playerID} non è nella lista attiva.")
        except Exception as e:
            print(f"❌ Errore imprevisto nel ClientsManager: {e}")

    def GetAll():
        return ClientsManager.PlayersList

    def GetCount():
        return len(ClientsManager.PlayersList)
