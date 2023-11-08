class ProductionLine:
    def __init__(self):
        self.WOs = {}

    def add_WO(self, id, palletization, total_pieces):
        self.WOs[id] = WO(id, palletization, total_pieces)

    def add_piece(self, WO_id, time):
        if WO_id in self.WOs:
            self.WOs[WO_id].add_piece(time)
