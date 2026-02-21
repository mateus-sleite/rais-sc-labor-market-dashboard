"""
Re-exports fato_rais.csv with comma as decimal separator
for compatibility with Power BI in Brazilian locale.
Uses semicolon as column separator.
"""
import pandas as pd
import os

PBI = "C:/Users/Mateus/Business Intelligence/projetos/desafio-analista-dados/dados_pbi"

print("Loading fato_rais.csv...")
fato = pd.read_csv(f"{PBI}/fato_rais.csv", low_memory=False)
print(f"Rows: {len(fato):,}")

print("\nCheck before correction:")
print(f"  remuneracao_media example: {fato['remuneracao_media'].iloc[0]}")
print(f"  remuneracao_media mean: {fato['remuneracao_media'].mean():.2f}")

# Re-export with column separator ; and decimal ,
output = f"{PBI}/fato_rais.csv"
print(f"\nExporting with separator ; and decimal comma...")
fato.to_csv(output, index=False, encoding="utf-8-sig", sep=";", decimal=",")

size = os.path.getsize(output) / 1024 / 1024
print(f"Saved: {size:.0f} MB")
print("\nIn Power BI, reimport using:")
print("  Delimiter: semicolon (;)")
print("  Decimals will already use comma (BR standard)")
