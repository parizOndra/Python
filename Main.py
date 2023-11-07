import pandas as pd
import random
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

class WO:
    def __init__(self, id, palletization, total_pieces):
        self.id = id
        self.palletization = palletization
        self.total_pieces = total_pieces
        self.pieces = 0
        self.pallets = 0

    def add_piece(self):
        self.pieces += 1
        self.total_pieces -= 1
        if self.pieces == self.palletization or self.total_pieces == 0:
            self.pallets += 1
            self.pieces = 0

class ProductionLine:
    def __init__(self):
        self.WOs = {}

    def add_WO(self, id, palletization, total_pieces):
        self.WOs[id] = WO(id, palletization, total_pieces)

    def add_piece(self, WO_id):
        if WO_id in self.WOs:
            self.WOs[WO_id].add_piece()

class Storage:
    def __init__(self):
        self.pallets = 0

    def add_pallet(self, WO):
        WO.pallets -= 1
        self.pallets += 1

def simulate(production_line, storage, sequence, times):
    in_progress_pallets_over_time = []
    for i, (WO_id, time) in enumerate(zip(sequence, times)):
        production_line.add_piece(WO_id)
        if production_line.WOs[WO_id].pallets > 0:
            storage.add_pallet(production_line.WOs[WO_id])
        
        # Sleduje počet rozdělaných palet v průběhu času
        in_progress_pallets = sum([1 for wo in production_line.WOs.values() if wo.pieces > 0])
        in_progress_pallets_over_time.append(in_progress_pallets)

    # Vytvoří datový rámec pandas
    df = pd.DataFrame({
        'Time': pd.to_datetime(times),
        'InProgressPallets': in_progress_pallets_over_time
    })

    # Vypočítá průměr
    df['Average'] = df['InProgressPallets'].rolling(window=50).mean()

    # Vypočítá trend pomocí lineární regrese
    df['TimeInt'] = df['Time'].factorize()[0]
    slope, intercept, r_value, p_value, std_err = stats.linregress(df['TimeInt'],df['InProgressPallets'])
    df['Trend'] = slope * df['TimeInt'] + intercept

    # Vykreslí graf
    ax = df.plot(x='Time', y=['InProgressPallets'])
    ax.grid(True)  # Přidá mřížku
    plt.show()

# Příklad použití
line = ProductionLine()
total_pieces = 0

# Načtení dat z CSV souborů
start_date = '2023-10-01'
end_date = '2023-11-10'

sequence_data = pd.read_excel (r'D:\Programming\Python\Projects\Python\Events.xlsx')
sequence_data = sequence_data[sequence_data['eventdted'].between(start_date, end_date)]
sequence_data = sequence_data.sort_values(by='eventdted', ascending=True)
sequence_data.to_csv (r'D:\Programming\Python\Projects\Python\Events.csv', index = None, header=True)

wo_data = pd.read_excel (r'D:\Programming\Python\Projects\Python\WOs.xlsx')
wo_data.to_csv (r'D:\Programming\Python\Projects\Python\WOs.csv', index = None, header=True)

# Přidáme pracovní příkazy z načtených dat
for i, row in wo_data.iterrows():
    pieces = row['Wo_Count']
    total_pieces += pieces
    line.add_WO(row['workorderno'], 10, pieces)         #Zatím simulace paletizace po 10ks

store = Storage()

# Generujeme data pro simulaci
sequence = sequence_data['workorderno'].tolist() # Seznam pracovních příkazů
times = sequence_data['eventdted'].tolist() # Časové razítka pro každý kus

simulate(line, store, sequence, times)
