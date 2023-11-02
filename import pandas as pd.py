import pandas as pd
import random
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class WO:
    def __init__(self, id, palletization):
        self.id = id
        self.palletization = palletization
        self.pieces = 0
        self.pallets = 0

    def add_piece(self):
        self.pieces += 1
        if self.pieces == self.palletization:
            self.pallets += 1
            self.pieces = 0

class ProductionLine:
    def __init__(self):
        self.WOs = {}

    def add_WO(self, id, palletization):
        self.WOs[id] = WO(id, palletization)

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
        'Time': times,
        'InProgressPallets': in_progress_pallets_over_time
    })

    # Vykreslí graf
    df.plot(x='Time', y='InProgressPallets')
    plt.show()


# Příklad použití
line = ProductionLine()
for i in range(1, 16): # Přidáme 15 pracovních příkazů s náhodnou paletizací od 1 do 24
    line.add_WO(f"WO{i}", random.randint(1, 24))
store = Storage()

# Generujeme náhodná data pro simulaci
sequence = [f"WO{random.randint(1, 15)}" for _ in range(1500)] # Náhodně vygenerovaná sekvence pracovních příkazů
times = [(datetime.now() + timedelta(minutes=x)).strftime("%Y-%m-%d %H:%M:%S") for x in range(1500)] # Časové razítka pro každý kus

simulate(line, store, sequence, times)
