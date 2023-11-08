import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import matplotlib.dates as mdates

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
    time_stamps = []

    for i, (WO_id, time) in enumerate(zip(sequence, times)):
        production_line.add_piece(WO_id, time)
        if production_line.WOs[WO_id].pallets > 0:
            storage.add_pallet(production_line.WOs[WO_id])
        
        # Sledování počtu rozdělaných palet
        in_progress_pallets = sum([1 for wo in production_line.WOs.values() if wo.pieces > 0])
        in_progress_pallets_over_time.append(in_progress_pallets)
        time_stamps.append(time)  # Přidání časového razítka

    # Vytvoření DataFrame
    in_progress_df = pd.DataFrame({
        'Time': time_stamps,
        'InProgressPallets': in_progress_pallets_over_time
    })

    completed_pallets_data = []
    for wo in production_line.WOs.values():
        completed_pallets_data.extend(wo.completed_pallets)

    return completed_pallets_data, in_progress_df


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
completed_pallets_data, in_progress_df = simulate(line, store, sequence, times)

# Uložení výsledků do CSV
completed_pallets_df = pd.DataFrame(completed_pallets_data)
completed_pallets_df['Duration'] = completed_pallets_df['Duration'].apply(lambda x: x.total_seconds())
output_filepath = os.path.join(current_dir, 'completed_pallets.csv')
completed_pallets_df.to_csv(output_filepath, index=False, date_format='%Y-%m-%d %H:%M:%S.%f')

print(f"Výsledky byly uloženy do souboru {output_filepath}")

plt.figure(figsize=(12, 6))
plt.plot(in_progress_df['Time'], in_progress_df['InProgressPallets'])
plt.title('Vývoj počtu rozdělaných palet v čase')
plt.xlabel('Čas')
plt.ylabel('Počet rozdělaných palet')

# Nastaví mřížku
plt.grid(True, linestyle='dotted', alpha=0.5)

# Nastaví formát časové osy X
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))  # Interval=6 hodin
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%a %H:%M'))  # Formát den v týdnu Hodina:Minu

# Otáčí popisky osy X
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig('in_progress_pallets_plot.png')
plt.show()