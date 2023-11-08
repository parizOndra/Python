import pandas as pd
import os
from datetime import datetime

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

class ProductionLine:
    def __init__(self):
        self.WOs = {}

    def add_WO(self, id, palletization, total_pieces):
        self.WOs[id] = WO(id, palletization, total_pieces)

    def add_piece(self, WO_id, time):
        if WO_id in self.WOs:
            self.WOs[WO_id].add_piece(time)

class Storage:
    def __init__(self):
        self.pallets = 0

    def add_pallet(self, WO):
        WO.pallets -= 1
        self.pallets += 1

def simulate(production_line, storage, sequence, times):
    in_progress_pallets_over_time = []

    for i, (WO_id, time) in enumerate(zip(sequence, times)):
        production_line.add_piece(WO_id, time)

        if production_line.WOs[WO_id].pallets > 0:
            storage.add_pallet(production_line.WOs[WO_id])

        in_progress_pallets = sum([1 for wo in production_line.WOs.values() if wo.pieces > 0])
        in_progress_pallets_over_time.append(in_progress_pallets)

    completed_pallets_data = []
    for wo in production_line.WOs.values():
        completed_pallets_data.extend(wo.completed_pallets)

    return completed_pallets_data

# Získání aktuálního pracovního adresáře
current_dir = os.getcwd()

# Definice relativních cest k souborům
wo_filepath = os.path.join(current_dir, 'WOs.csv')
events_filepath = os.path.join(current_dir, 'Events.csv')

# Načtení dat
wo_data = pd.read_csv(wo_filepath)
events_data = pd.read_csv(events_filepath)
events_data['eventdted'] = pd.to_datetime(events_data['eventdted'])

# Initialize the production line and storage
line = ProductionLine()
store = Storage()

# Add work orders to the production line with the standard palletization
palletization_standard = 10
for i, row in wo_data.iterrows():
    line.add_WO(row['workorderno'], palletization_standard, row['Wo_Count'])

# Generate data for simulation from the events
sequence = events_data['workorderno'].tolist()  # List of work orders from the events
times = events_data['eventdted'].tolist()       # Timestamps for each event

# Run the simulation with actual data
completed_pallets_data = simulate(line, store, sequence, times)

# Convert the completed pallets data to a DataFrame for better visualization
completed_pallets_df = pd.DataFrame(completed_pallets_data)
print(completed_pallets_df.head())  # Display the first few rows of the completed pallets dataframe
