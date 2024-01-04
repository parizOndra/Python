import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime
import seaborn as sns
import numpy as np

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
        # Pokud ještě nebyl dosažen limit paletizace a zbývají kusy k dokončení
        if self.pieces < self.palletization and self.total_pieces > 0:
            if self.pieces == 0:
                self.start_time = time  # Začátek nové palety

            self.pieces += 1
            self.total_pieces -= 1

            # Kontrola, zda je paleta kompletní
            if self.pieces == self.palletization or self.total_pieces == 0:
                # Zaznamenání dokončené palety
                real_pieces = min(self.pieces, self.palletization)

                self.completed_pallets.append({
                    'WO': self.id,
                    'Palletization': self.palletization,
                    'Pieces': real_pieces,
                    'PalletID': self.pallets,
                    'StartTime': self.start_time,
                    'EndTime': time,
                    'Duration': (time - self.start_time).total_seconds(),
                    'IsFull': self.pieces == self.palletization
                })
                # Reset kusů pro další paletu
                self.pieces = 0
                self.pallets += 1  # Zvýšení počtu palet pro toto WO

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
        self.trucks = []
        self.current_truck = {'id': 'Truck_A', 'start_time': None, 'end_time': None, 'pallets_loaded': 0}

    def add_pallet(self, WO, time):
        WO.pallets -= 1
        self.pallets += 1
        self.current_truck['pallets_loaded'] += 1
        if self.current_truck['pallets_loaded'] == 1:
            self.current_truck['start_time'] = time
        if self.current_truck['pallets_loaded'] == 20 or self.pallets == 0:
            self.current_truck['end_time'] = time
            self.trucks.append(self.current_truck.copy())
            # Reset the current truck
            self.current_truck = {'id': f'Truck_{len(self.trucks) + 1}', 'start_time': None, 'end_time': None, 'pallets_loaded': 0}

def simulate(production_line, storage, sequence, times):
    in_progress_pallets_over_time = []
    time_stamps = []
    
    for i, (WO_id, time) in enumerate(zip(sequence, times)):
        production_line.add_piece(WO_id, time)
        # Kontrola, zda jsou na produkční lince palety k přidání do skladu
        if production_line.WOs[WO_id].pallets > 0:
            # Přidání palety do skladu s předáním aktuálního času
            storage.add_pallet(production_line.WOs[WO_id], time)
        
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

# Definice cest k XLSX souborům
wo_xlsx_filepath = os.path.join(current_dir, 'WOs - Sheet1.csv')
events_xlsx_filepath = os.path.join(current_dir, 'Events - Sheet1.csv')

# Načtení dat z XLSX souborů
wo_data = pd.read_csv(wo_xlsx_filepath)
events_data = pd.read_csv(events_xlsx_filepath)

wo_data['workorderno'] = wo_data['workorderno'].astype(str)
events_data['workorderno'] = events_data['workorderno'].astype(str)

events_data['eventdted'] = pd.to_datetime(events_data['eventdted'], format='%Y-%m-%d %H:%M:%S.%f')
events_data = events_data.sort_values(by='eventdted')

# Initialize the production line and storage
line = ProductionLine()
store = Storage()

# Add work orders to the production line with the standard palletization
for i, row in wo_data.iterrows():
    line.add_WO(row['workorderno'], row['Pcs On Pallet'], row['Wo_Count'])

# Generate data for simulation from the events
sequence = events_data['workorderno'].tolist()
times = events_data['eventdted'].tolist()

# Run the simulation with actual data
completed_pallets_data, in_progress_df = simulate(line, store, sequence, times)

# Uložení informací o kamionech do DataFrame a CSV souboru
truck_data = pd.DataFrame(store.trucks)
truck_data['Duration'] = truck_data['end_time'] - truck_data['start_time']
truck_data['DurationFormatted'] = truck_data['Duration'].apply(
    lambda x: f"{int(x.total_seconds() // 3600)}:{int((x.total_seconds() % 3600) // 60)}"
)

# Uložení dat o kamionech
truck_data.to_csv(os.path.join(current_dir, 'Trucks.csv'), index=False)

# Výpočet statistik
completed_pallets_df = pd.DataFrame(completed_pallets_data)
average_duration = completed_pallets_df['Duration'].mean()
lower_quantile = completed_pallets_df['Duration'].quantile(0.25)
upper_quantile = completed_pallets_df['Duration'].quantile(0.75)

# Formátování výstupu
average_duration_hms = seconds_to_hms(average_duration)
lower_quantile_hms = seconds_to_hms(lower_quantile)
upper_quantile_hms = seconds_to_hms(upper_quantile)

#-------------------------------pallet_completion_time_statistics-----------------------------------------
plt.figure(figsize=(8, 5))
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

#-------------------------------Time Series Plot for In-Progress Pallets--------------------------------------
plt.figure(figsize=(15, 5))
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

#-------------------------------Histogram of Pallet Completion Times------------------------------------------
plt.figure(figsize=(20, 5))
ax = sns.histplot(completed_pallets_df['Duration'], bins=70)
for p in ax.patches:
    ax.annotate(f'{int(p.get_height())}', 
                (p.get_x() + p.get_width() / 2., p.get_height()), 
                ha = 'center', va = 'center', 
                xytext = (0, 5), 
                textcoords = 'offset points')
plt.title('Histogram of Pallet Completion Times')
plt.xlabel('Duration in Seconds')
plt.ylabel('Frequency')

# Calculate bin edges and set x-ticks
min_duration = completed_pallets_df['Duration'].min()
max_duration = completed_pallets_df['Duration'].max()
bin_width = (max_duration - min_duration) / 70  # assuming 70 bins
bin_edges = np.arange(min_duration, max_duration + bin_width, bin_width)
plt.xticks(bin_edges, rotation=90)

plt.tight_layout()
plt.savefig('pallet_completion_times_histogram.png')
plt.show()

#-------------------------------Truck visualization------------------------------------------
# Make sure 'start_time' is a datetime column
truck_data['start_time'] = pd.to_datetime(truck_data['start_time'])

# Resampling to get the count of trucks per 3 hours
trucks_per_3hours = truck_data.set_index('start_time').resample('3H').size()

# Plotting the data
plt.figure(figsize=(12, 6))
trucks_per_3hours.plot(kind='bar')
plt.title('Number of Trucks per 3 Hours')
plt.xlabel('3-Hour Interval')
plt.ylabel('Number of Trucks')
plt.xticks(rotation=90)
plt.tight_layout()

# Show the plot
plt.show()
#-------------------------------Save CSV pallets------------------------------------------
completed_pallets_df = pd.DataFrame(completed_pallets_data)
# Převod StartTime a EndTime na formát HH:MM:SS
completed_pallets_df['StartTime'] = completed_pallets_df['StartTime'].dt.strftime('%Y-%m-%d %H:%M:%S')
completed_pallets_df['EndTime'] = completed_pallets_df['EndTime'].dt.strftime('%Y-%m-%d %H:%M:%S')

# Převod Duration na formát HH:MM:SS
completed_pallets_df['Duration'] = completed_pallets_df['Duration'].apply(seconds_to_hms)

# Uložení do CSV
completed_pallets_df.to_csv(os.path.join(current_dir, 'Completed_Pallets.csv'), index=False)
