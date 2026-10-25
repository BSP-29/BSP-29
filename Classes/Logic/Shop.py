import json, random
class Shop:
    """
    << Shop Offers IDs List >>

    0 = Free Brawl Box
    1 = Gold
    2 = Random Brawler
    3 = Brawler
    4 = Skin
    5 = StarPower/ Gadget
    6 = Brawl Box
    7 = Tickets (not working anymore)
    8 = Power Points (for a specific brawler)
    9 = Token Doubler
    10 = Mega Box
    11 = Keys (???)
    12 = Power Points
    13 = EventSlot (???)
    14 = Big Box
    15 = AdBox (not working anymore)
    16 = Gems
    19 = Pin for Brawler
    20 = Pin Collection
    21 = Pin Pack
    22 = Pins Pack For Brawler
    23 = Pin Common (???)
    24 = Shop Skin Offer (May Not Work)
    94 = Skin???
    

    << Shop Offers BGR List >>

    Token Offer = offer_generic
    Special Offer = offer_special
    Starpoint Offer = offer_legendary
    Coin Offer = offer_coins(in v29 like offer_moon_festival)
    Gem Offer = offer_gems
    Box Offer = offer_boxes
    Brawler Offer = offer_finals
    LNY Offer = offer_lny
    Archive Offer = offer_archive
    Chromatic = offer_chromatic
    Moon Festival = offer_moon_festival
    Xmas = offer_xmas
    


    ET is Extra Text

    """

    gold = [
        {
            'Cost': 20,
            'Amount': 300
        },

        {
            'Cost': 50,
            'Amount': 800
        },

        {
            'Cost': 140,
            'Amount': 2400
        },

        {
            'Cost': 280,
            'Amount': 5200
        },

    ]

    boxes = [
        {
            'Name': 'Big Box',
            'Cost': 30,
            'Multiplier': 3
        },

        {
            'Name': 'Mega Box',
            'Cost': 80,
            'Multiplier': 10
        }

    ]


    token_doubler = {

        'Cost': 40,
        'Amount': 1500
    }

    def loadOffers(self):
        self.offers=[]
        with open("Logic/offers.json", "r",encoding='utf-8') as f:
            data = json.load(f)
            for i in data.values():
                self.offers.append(i)
    def UpdateOfferData(self, i):
        with open("Logic/offers.json", "r",encoding='utf-8') as f:
            data = json.load(f)
        data[str(i)]["WhoBuyed"].append(int(self.player.LowID))
        with open("Logic/offers.json", "w",encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    def RemoveOffer(self, i):
        with open("Logic/offers.json", "r") as f:
            data = json.load(f, indent=4,)
        data.pop(str(i))
        with open("Logic/offers.json", "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)



    def EncodeShopOffers(self):
        Shop.loadOffers(self)
        wow = self.offers
        count = len(wow)
        self.writeVInt(count)
        for i in range(count):
            item = wow[i]
            if item['ID'][0] != 0 and item['ID'][1] != 0 and item['ID'][2] != 0:
                self.writeVInt(3)
                self.writeVInt(item['ID'][0]) # ItemID
                self.writeVInt(item['Multiplier'][0]) # Ammount
                self.writeDataReference(16, item['BrawlerID'][0])
                self.writeVInt(item['SkinID'][0]) # ItemID
                self.writeVInt(item['ID'][1]) # ItemID
                self.writeVInt(item['Multiplier'][1]) # Ammount
                self.writeDataReference(16, item['BrawlerID'][1])
                self.writeVInt(item['SkinID'][1]) # ItemID
                self.writeVInt(item['ID'][2]) # ItemID
                self.writeVInt(item['Multiplier'][2]) # Ammount
                self.writeDataReference(16, item['BrawlerID'][2])
                self.writeVInt(item['SkinID'][2]) # ItemID

            elif item['ID'][0] != 0 and item['ID'][1] != 0:
                self.writeVInt(2)
                self.writeVInt(item['ID'][0]) # ItemID
                self.writeVInt(item['Multiplier'][0]) # Ammount
                self.writeDataReference(16, item['BrawlerID'][0])
                self.writeVInt(item['SkinID'][0]) # ItemID
                self.writeVInt(item['ID'][1]) # ItemID
                self.writeVInt(item['Multiplier'][1]) # Ammount
                self.writeDataReference(16, item['BrawlerID'][1])
                self.writeVInt(item['SkinID'][1]) # ItemID

            else:
                if getattr(self.player, "UnlockedBrawlers", {}).get(str(int(item["BrawlerID"][0])), 0) == 1:
                    self.writeVInt(1)
                    self.writeVInt(item['ID'][0])
                    self.writeVInt(item['Multiplier'][0])
                    self.writeDataReference(16, item['BrawlerID'][0])
                    self.writeVInt(item['SkinID'][0])
                else:
                    self.writeVInt(1)
                    self.writeVInt(1) # ItemID
                    self.writeVInt(0) # Ammount
                    self.writeDataReference(16, 0)
                    self.writeVInt(0) # ItemID
                    
            self.writeVInt(item['ShopType'])  # [0 = Offer, 2 = Skins 3 = Star Shop]

            self.writeVInt(item['Cost'])  # Cost
            self.writeVInt(172800)

            self.writeVInt(0)# Offer View | 0 = Absolutely "NEW", 1 = "NEW", 2 = Viewed
            self.writeVInt(100)
            if self.player.LowID in item["WhoBuyed"]:
                self.writeBoolean(True)
            else:
                if getattr(self.player, "UnlockedBrawlers", {}).get(str(int(item["BrawlerID"][0])), 0) == 0 or getattr(self.player, "UnlockedSkins", {}).get(str(int(item["SkinID"][0])), 0) == 1:
                    self.writeBoolean(True)
                else:
                    self.writeBoolean(False)
        
            self.writeBoolean(False)
            if getattr(self.player, "UnlockedBrawlers", {}).get(str(int(item["BrawlerID"][0])), 0) == 0:
                self.writeVInt(0)
            else:
                self.writeVInt(item['ShopDisplay'])# [0 = Normal, 1 = Daily Deals]
            self.writeBoolean(item['OldCost'])
            self.writeVInt(0)

            self.writeInt(0)

            self.write_string_reference(item['OfferTitle'])

            self.writeBoolean(False)
            self.writeString(item['OfferBGR'])
            self.writeVInt(0)
            self.writeBoolean(False)
            self.writeVInt(0)
            self.writeVInt(0)
		#shopend