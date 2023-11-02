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
    df.plot(x='Time', y=['InProgressPallets', 'Average', 'Trend'])
    plt.show()

# Příklad použití
line = ProductionLine()
total_pieces = 0

# Přidáme 1000 pracovních příkazů s náhodnou paletizací od 1 do 24 a náhodným počtem kusů od 25 do 100
for i in range(1, 1001):
    pieces = random.randint(25, 100)
    total_pieces += pieces
    line.add_WO(f"WO{i}", random.randint(1, 24), pieces)

store = Storage()

# Generujeme data pro simulaci
sequence = []
for i in range(1, 1001):
    sequence.extend([f"WO{i}"] * line.WOs[f"WO{i}"].total_pieces) # Přidáme do sekvence správný počet kusů pro každé WO

random.shuffle(sequence) # Zamícháme sekvenci
times = [(datetime.now() + timedelta(minutes=x)).strftime("%Y-%m-%d %H:%M:%S") for x in range(total_pieces)] # Časové razítka pro každý kus

simulate(line, store, sequence, times)