import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime
import seaborn as sns

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
                'Duration': (time - self.start_time).total_seconds()  # Duration of palletization in seconds
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
        
        in_progress_pallets = sum([1 for wo in production_line.WOs.values() if wo.pieces > 0])
        in_progress_pallets_over_time.append(in_progress_pallets)
        time_stamps.append(time)

    in_progress_df = pd.DataFrame({
        'Time': time_stamps,
        'InProgressPallets': in_progress_pallets_over_time
    })

    completed_pallets_data = []
    for wo in production_line.WOs.values():
        completed_pallets_data.extend(wo.completed_pallets)

    return completed_pallets_data, in_progress_df

# Převod sekund na formát hh:mm:ss
def seconds_to_hms(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

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
sequence = events_data['workorderno'].tolist()
times = events_data['eventdted'].tolist()

# Run the simulation with actual data
completed_pallets_data, in_progress_df = simulate(line, store, sequence, times)

# Výpočet statistik
completed_pallets_df = pd.DataFrame(completed_pallets_data)
average_duration = completed_pallets_df['Duration'].mean()
lower_quantile = completed_pallets_df['Duration'].quantile(0.25)
upper_quantile = completed_pallets_df['Duration'].quantile(0.75)

# Formátování výstupu
average_duration_hms = seconds_to_hms(average_duration)
lower_quantile_hms = seconds_to_hms(lower_quantile)
upper_quantile_hms = seconds_to_hms(upper_quantile)

# pallet_completion_time_statistics
plt.figure(figsize=(10, 5))
sns.barplot(x=['Average Duration', 'Lower Quantile (25%)', 'Upper Quantile (75%)'],
            y=[average_duration, lower_quantile, upper_quantile])
plt.title('Pallet Completion Time Statistics')
plt.ylabel('Duration in Seconds')
plt.xlabel('Statistic')
plt.text(0, average_duration, average_duration_hms, ha='center', va='bottom')
plt.text(1, lower_quantile, lower_quantile_hms, ha='center', va='bottom')
plt.text(2, upper_quantile, upper_quantile_hms, ha='center', va='bottom')
plt.tight_layout()
plt.savefig('pallet_completion_time_statistics.png')
plt.show()

# Time Series Plot for In-Progress Pallets with 6-hour Grid
plt.figure(figsize=(10, 5))
sns.lineplot(data=in_progress_df, x='Time', y='InProgressPallets')
plt.title('In-Progress Pallets Over Time')
plt.ylabel('Number of In-Progress Pallets')
plt.xlabel('Time')
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
plt.grid(which='major', linestyle='--', linewidth=0.5)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('in_progress_pallets_over_time.png')
plt.show()

# Histogram of Pallet Completion Times
plt.figure(figsize=(10, 5))
ax = sns.histplot(completed_pallets_df['Duration'], bins=50)
for p in ax.patches:
    ax.annotate(f'{int(p.get_height())}', 
                (p.get_x() + p.get_width() / 2., p.get_height()), 
                ha = 'center', va = 'center', 
                xytext = (0, 5), 
                textcoords = 'offset points')
plt.title('Histogram of Pallet Completion Times')
plt.xlabel('Duration in Seconds')
plt.ylabel('Frequency')
plt.tight_layout()
plt.savefig('pallet_completion_times_histogram.png')
plt.show()