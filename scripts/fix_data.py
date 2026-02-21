"""
Corrections based on integrity validation
"""
import pandas as pd
import os

PBI = "C:/Users/Mateus/Business Intelligence/projetos/desafio-analista-dados/dados_pbi"

print("Loading fato_rais.csv...")
fato = pd.read_csv(f"{PBI}/fato_rais.csv", low_memory=False)
print(f"Initial rows: {len(fato):,}")

# ============================================================
# 1. INVESTIGATE DUPLICATES
# ============================================================
print("\n" + "=" * 60)
print("1. INVESTIGATING DUPLICATES")
print("=" * 60)

dupes = fato[fato.duplicated(keep=False)]
print(f"Rows involved in duplicates: {len(dupes):,}")
print(f"\nDistribution by year:")
print(dupes["ano"].value_counts().sort_index().to_string())

print(f"\nDuplicate example:")
sample_dupe = fato[fato.duplicated(keep=False)].head(4)
print(sample_dupe.to_string())

# Remove duplicates (keep first occurrence)
antes = len(fato)
fato = fato.drop_duplicates()
depois = len(fato)
print(f"\nRemoved: {antes - depois:,} duplicates")
print(f"Remaining rows: {depois:,}")

# ============================================================
# 2. INVESTIGATE REMUNERATION = 0
# ============================================================
print("\n" + "=" * 60)
print("2. INVESTIGATING REMUNERATION = 0")
print("=" * 60)

zeros = fato[fato["remuneracao_media"] == 0]
print(f"Records with remuneration = 0: {len(zeros):,}")
print(f"\nBy active/inactive employment:")
print(zeros["vinculo_ativo"].value_counts().to_string())
print(f"\nBy age group (code):")
print(zeros["cod_faixa_etaria"].value_counts().sort_index().to_string())
print(f"\nBy education level (code):")
print(zeros["cod_escolaridade"].value_counts().sort_index().head(5).to_string())

# Decision: keep, as they may be apprentices, interns or records
# terminated at the beginning of the period. Do not exclude, but document.
print("\n-> DECISION: Keep. May be apprentices/interns or quickly")
print("   terminated records. In Power BI, active employment filters")
print("   already eliminate the majority.")

# ============================================================
# 3. INVESTIGATE REMUNERATION > 100k
# ============================================================
print("\n" + "=" * 60)
print("3. INVESTIGATING REMUNERATION > 100k")
print("=" * 60)

outliers = fato[fato["remuneracao_media"] > 100000]
print(f"Records > R$100k: {len(outliers):,}")
print(f"\nTop 10 remunerations:")
top = outliers.nlargest(10, "remuneracao_media")[["ano", "cod_municipio", "remuneracao_media", "cod_cnae_classe"]]
print(top.to_string())

# Check if it is a very small percentage
pct = len(outliers) / len(fato) * 100
print(f"\n-> They represent {pct:.3f}% of the total.")
print("-> DECISION: Keep. They are official RAIS data (senior executives, etc.)")
print("   If they distort visuals, filter in Power BI.")

# ============================================================
# 4. FIX DIMENSIONS (add missing codes)
# ============================================================
print("\n" + "=" * 60)
print("4. FIXING DIMENSIONS")
print("=" * 60)

# dim_sexo
dim_sexo = pd.read_csv(f"{PBI}/dim_sexo.csv")
if 9 not in dim_sexo["cod_sexo"].values:
    dim_sexo = pd.concat([dim_sexo, pd.DataFrame([{"cod_sexo": 9, "sexo": "Não informado"}])], ignore_index=True)
    dim_sexo.to_csv(f"{PBI}/dim_sexo.csv", index=False, encoding="utf-8-sig")
    print("  dim_sexo: added code 9 = 'Não informado'")

# dim_raca
dim_raca = pd.read_csv(f"{PBI}/dim_raca.csv")
if 99 not in dim_raca["cod_raca"].values:
    dim_raca = pd.concat([dim_raca, pd.DataFrame([{"cod_raca": 99, "raca": "Não informado"}])], ignore_index=True)
    dim_raca.to_csv(f"{PBI}/dim_raca.csv", index=False, encoding="utf-8-sig")
    print("  dim_raca: added code 99 = 'Não informado'")

# dim_faixa_etaria
dim_faixa = pd.read_csv(f"{PBI}/dim_faixa_etaria.csv")
if 99 not in dim_faixa["cod_faixa_etaria"].values:
    dim_faixa = pd.concat([dim_faixa, pd.DataFrame([{"cod_faixa_etaria": 99, "faixa_etaria": "Não classificado"}])], ignore_index=True)
    dim_faixa.to_csv(f"{PBI}/dim_faixa_etaria.csv", index=False, encoding="utf-8-sig")
    print("  dim_faixa_etaria: added code 99 = 'Não classificado'")

# dim_escolaridade
dim_esc = pd.read_csv(f"{PBI}/dim_escolaridade.csv")
if 99 not in dim_esc["cod_escolaridade"].values:
    dim_esc = pd.concat([dim_esc, pd.DataFrame([{"cod_escolaridade": 99, "escolaridade": "Não classificado"}])], ignore_index=True)
    dim_esc.to_csv(f"{PBI}/dim_escolaridade.csv", index=False, encoding="utf-8-sig")
    print("  dim_escolaridade: added code 99 = 'Não classificado'")

# ============================================================
# 5. SAVE CORRECTED FACT TABLE (without duplicates)
# ============================================================
print("\n" + "=" * 60)
print("5. SAVING CORRECTED FACT TABLE")
print("=" * 60)

fato.to_csv(f"{PBI}/fato_rais.csv", index=False, encoding="utf-8-sig")
size = os.path.getsize(f"{PBI}/fato_rais.csv") / 1024 / 1024
print(f"  fato_rais.csv: {len(fato):,} rows, {size:.0f} MB")

# ============================================================
# 6. CORRECTIONS SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("CORRECTIONS SUMMARY")
print("=" * 60)
print("""
CORRECTED:
  - Removed 144,935 duplicate rows
  - dim_sexo: added code 9 (Nao informado)
  - dim_raca: added code 99 (Nao informado) — 612K records
  - dim_faixa_etaria: added code 99 (Nao classificado)
  - dim_escolaridade: added code 99 (Nao classificado)

KEPT (with justification):
  - Remuneration = 0 (531K): apprentices/interns/short-term records
  - Remuneration > 100k (3,743): official data, minimal percentage
  - mes_desligamento null (69%): expected for active employment records
  - mes_admissao = 0: records hired before the reference year
""")
