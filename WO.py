class WO:
    def __init__(self, id, palletization, total_pieces):
        self.id = id
        self.palletization = palletization
        self.total_pieces = total_pieces
        self.pieces = 0
        self.pallets = 0
        self.completed_pallets = []  # List of completed pallets
        self.start_time = None  # Start time of a pallet

    def add_piece(self, time):
        if self.pieces == 0:
            self.start_time = time  # Start of a new pallet
        self.pieces += 1
        self.total_pieces -= 1
        if self.pieces == self.palletization or self.total_pieces == 0:
            self.pallets += 1
            self.pieces = 0
            self.completed_pallets.append({
                'WO': self.id,
                'Pieces': self.palletization,
                'PalletID': self.pallets,
                'StartTime': self.start_time,
                'EndTime': time,
                'Duration': time - self.start_time  # Duration of palletization
            })