class rarity():

    def __init__(self, sym, name, display_order):
        self.sym = sym
        self.name = name
        self.display_order = display_order

def rarity_list():

    ls = []

    ls.append(rarity('L', 'Basic Land', 10))
    ls.append(rarity('C', 'Common', 20))
    ls.append(rarity('U', 'Uncommmon', 30))
    ls.append(rarity('R', 'Rare', 40))
    ls.append(rarity('M', 'Mythic Rare', 50))
    ls.append(rarity('T', 'Timeshifted', 60))
    ls.append(rarity('S', 'Special', 70))

    return ls
