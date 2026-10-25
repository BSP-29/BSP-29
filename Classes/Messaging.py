import traceback


# Messages that make the client render the lobby. If one of these lands on top
# of the loading screen the client is pulled back out of the match and the
# battle never starts. The call sites that broadcast a team snapshot have their
# own guard, but there are enough of them that the invariant is enforced here
# as well, so a path nobody remembered cannot reintroduce the stall.
_LOBBY_ONLY_MESSAGES = (24124, 23457)


class Messaging:
    def writeHeader(message, payloadLen):
        message.messageBuffer += message.getMessageType().to_bytes(2, 'big', signed=True)
        message.messageBuffer += payloadLen.to_bytes(3, 'big', signed=True)
        message.messageBuffer += message.messageVersion.to_bytes(2, 'big', signed=True)

    def readHeader(headerBytes):
        headerData = []
        headerData.append(int.from_bytes(headerBytes[:2], 'big', signed=True))
        headerData.append(int.from_bytes(headerBytes[2:5], 'big', signed=True))
        return headerData

    def _suppressed_by_battle(messageType, player):
        """Drop a lobby snapshot aimed at a client that is loading a battle.

        Returns True only when the message was definitively skipped. Any error
        resolving the battle state falls through to sending, because a failed
        lookup must not silently swallow a legitimate lobby message.
        """
        if messageType not in _LOBBY_ONLY_MESSAGES or player is None:
            return False
        try:
            from Classes.TeamMatchmaking import member_is_in_battle
            if member_is_in_battle(player):
                return True
        except Exception:
            return False
        return False

    def sendMessage(messageType, fields, cryptoInit, player=None, calling_instance=None):
        from Classes.Logic.LogicLaserMessageFactory import LogicLaserMessageFactory

        if Messaging._suppressed_by_battle(messageType, player):
            print(f"[MSG] {messageType} withheld: player "
                  f"{getattr(player, 'LowID', '?')} is already loading a battle")
            return

        # Prendi il client
        client = None
        if fields and "Socket" in fields:
            client = fields["Socket"]
        elif calling_instance is not None and hasattr(calling_instance, "client"):
            client = calling_instance.client
        elif player is not None and hasattr(player, "client"):
            client = player.client
        else:
            print(f"[ERROR] sendMessage {messageType}: no client found")
            return

        message = LogicLaserMessageFactory.createMessageByType(messageType, b'')
        if message is None:
            print(f"[ERROR] sendMessage {messageType}: no message encoder")
            return

        # --- ENCODE ---
        # When this message is being dumped, the encoder is run under a write
        # trace so the printed field list is the list the encoder actually
        # produced. Re-parsing the finished payload would be a second
        # implementation of the layout, and the two can disagree.
        trace = None
        try:
            from Classes.Logic.PacketDump import should_dump as _should_dump
            watched = _should_dump(messageType)
        except Exception:
            watched = False

        try:
            encode_fields = fields if fields is not None else {}
            encode_kwargs = {}
            if player is not None:
                encode_kwargs["player"] = player

            if watched:
                from Classes.ByteStream import _WriteTrace
                trace = _WriteTrace(message)
                with trace:
                    message.encode(encode_fields, **encode_kwargs)
            else:
                message.encode(encode_fields, **encode_kwargs)
        except Exception:
            print(f"[ERROR] sendMessage {messageType} ENCODE failed "
                  f"for player {getattr(player, 'LowID', '?')}")
            print(traceback.format_exc())
            return

        # --- DUMP (before encryption, so the printed bytes are the plaintext) ---
        try:
            from Classes.Logic.PacketDump import dump as _dump, render_trace as _render
            if watched:
                if trace is not None and trace.entries:
                    _render(trace, messageType, message.messagePayload)
                else:
                    _dump(messageType, message.messagePayload)
        except Exception:
            traceback.print_exc()

        # --- ENCRYPT ---
        try:
            if messageType == 20100:
                cryptoInit.setSessionKey(message.getSessionKey())

            # === FIX: Estrai il crypto da cryptoInit se necessario ===
            crypto = cryptoInit
            
            # Se cryptoInit ha un attributo crypto che ha encryptServer
            if hasattr(cryptoInit, 'crypto') and hasattr(cryptoInit.crypto, 'encryptServer'):
                crypto = cryptoInit.crypto
            # Se cryptoInit ha direttamente encryptServer
            elif hasattr(cryptoInit, 'encryptServer'):
                crypto = cryptoInit
            # Se cryptoInit è una connessione con .crypto
            elif hasattr(cryptoInit, 'crypto') and hasattr(cryptoInit.crypto, 'encrypt'):
                crypto = cryptoInit.crypto
            else:
                # Cerca in tutti gli attributi di cryptoInit
                found = False
                for attr_name in dir(cryptoInit):
                    if attr_name.startswith('_'):
                        continue
                    attr = getattr(cryptoInit, attr_name)
                    if hasattr(attr, 'encryptServer'):
                        crypto = attr
                        found = True
                        print(f"[Messaging] Found encryptServer in {attr_name}")
                        break
                
                if not found:
                    print(f"[ERROR] sendMessage {messageType}: No encryptServer found in {type(cryptoInit)}")
                    print(f"[ERROR] Available attributes: {[a for a in dir(cryptoInit) if not a.startswith('_')]}")
                    return

            message.messagePayload = crypto.encryptServer(
                message.getMessageType(),
                message.messagePayload
            )
        except Exception as e:
            print(f"[ERROR] sendMessage {messageType} ENCRYPT failed "
                  f"for player {getattr(player, 'LowID', '?')}")
            print(f"Error: {e}")
            print(traceback.format_exc())
            return

        print(f"[DEBUG] sendMessage {messageType} payload len before header: {len(message.messagePayload)}")

        # --- HEADER + BUFFER ---
        Messaging.writeHeader(message, len(message.messagePayload))
        message.messageBuffer += message.messagePayload

        # --- SEND ---
        try:
            print(f"[DEBUG] sendMessage {messageType} total len: {len(message.messageBuffer)}")
            client.send(message.messageBuffer)
        except Exception:
            print(f"[ERROR] sendMessage {messageType} SEND failed "
                  f"for player {getattr(player, 'LowID', '?')}")
            print(traceback.format_exc())
