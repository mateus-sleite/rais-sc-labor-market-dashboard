"""
Optimizes treated data for Power BI using a star schema.
Splits into fact + dimensions to reduce size and improve performance.
"""
import pandas as pd
import os
import time

INPUT = "C:/Users/Mateus/Business Intelligence/projetos/desafio-analista-dados/dados_tratados"
OUTPUT = "C:/Users/Mateus/Business Intelligence/projetos/desafio-analista-dados/dados_pbi"
os.makedirs(OUTPUT, exist_ok=True)

print("Loading rais_tratada.csv (may take 1-2 min)...")
t0 = time.time()
df = pd.read_csv(f"{INPUT}/rais_tratada.csv", low_memory=False)
print(f"Loaded: {len(df):,} rows in {time.time()-t0:.0f}s")

# ============================================================
# FACT TABLE — codes and measures only
# ============================================================
print("\nCreating fact table...")
fato = df[[
    "ano",
    "cod_municipio",
    "vinculo_ativo",
    "remuneracao_media",
    "cod_cnae_classe",
    "cod_cnae_divisao",
    "cod_sexo",
    "cod_raca",
    "cod_faixa_etaria",
    "cod_escolaridade",
    "tempo_emprego_meses",
    "mes_admissao",
    "mes_desligamento"
]].copy()

fato_path = f"{OUTPUT}/fato_rais.csv"
fato.to_csv(fato_path, index=False, encoding="utf-8-sig")
print(f"  -> fato_rais.csv: {os.path.getsize(fato_path)/1024/1024:.0f} MB ({len(fato):,} rows)")

# ============================================================
# MUNICIPALITY/REGION DIMENSION
# ============================================================
print("\nCreating municipality dimension...")
dim_mun = df[["cod_municipio", "municipio", "regiao_imediata", "regiao_intermediaria"]].drop_duplicates()
dim_mun = dim_mun.sort_values("cod_municipio").reset_index(drop=True)
dim_mun_path = f"{OUTPUT}/dim_municipio.csv"
dim_mun.to_csv(dim_mun_path, index=False, encoding="utf-8-sig")
print(f"  -> dim_municipio.csv: {len(dim_mun)} records")

# ============================================================
# CNAE DIMENSION
# ============================================================
print("\nCreating CNAE dimension...")
dim_cnae = df[["cod_cnae_classe", "cnae_classe", "cod_cnae_divisao", "cnae_divisao"]].drop_duplicates()
dim_cnae = dim_cnae.dropna(subset=["cod_cnae_classe"]).sort_values("cod_cnae_classe").reset_index(drop=True)
dim_cnae_path = f"{OUTPUT}/dim_cnae.csv"
dim_cnae.to_csv(dim_cnae_path, index=False, encoding="utf-8-sig")
print(f"  -> dim_cnae.csv: {len(dim_cnae)} records")

# ============================================================
# GENDER DIMENSION
# ============================================================
print("\nCreating gender dimension...")
dim_sexo = df[["cod_sexo", "sexo"]].drop_duplicates().dropna().sort_values("cod_sexo").reset_index(drop=True)
dim_sexo_path = f"{OUTPUT}/dim_sexo.csv"
dim_sexo.to_csv(dim_sexo_path, index=False, encoding="utf-8-sig")
print(f"  -> dim_sexo.csv: {len(dim_sexo)} records")

# ============================================================
# RACE/COLOR DIMENSION
# ============================================================
print("\nCreating race/color dimension...")
dim_raca = df[["cod_raca", "raca"]].drop_duplicates().dropna().sort_values("cod_raca").reset_index(drop=True)
dim_raca_path = f"{OUTPUT}/dim_raca.csv"
dim_raca.to_csv(dim_raca_path, index=False, encoding="utf-8-sig")
print(f"  -> dim_raca.csv: {len(dim_raca)} records")

# ============================================================
# AGE GROUP DIMENSION
# ============================================================
print("\nCreating age group dimension...")
dim_faixa = df[["cod_faixa_etaria", "faixa_etaria"]].drop_duplicates().dropna().sort_values("cod_faixa_etaria").reset_index(drop=True)
dim_faixa_path = f"{OUTPUT}/dim_faixa_etaria.csv"
dim_faixa.to_csv(dim_faixa_path, index=False, encoding="utf-8-sig")
print(f"  -> dim_faixa_etaria.csv: {len(dim_faixa)} records")

# ============================================================
# EDUCATION LEVEL DIMENSION
# ============================================================
print("\nCreating education level dimension...")
dim_esc = df[["cod_escolaridade", "escolaridade"]].drop_duplicates().dropna().sort_values("cod_escolaridade").reset_index(drop=True)
dim_esc_path = f"{OUTPUT}/dim_escolaridade.csv"
dim_esc.to_csv(dim_esc_path, index=False, encoding="utf-8-sig")
print(f"  -> dim_escolaridade.csv: {len(dim_esc)} records")

# ============================================================
# SUMMARY
# ============================================================
total_size = sum(
    os.path.getsize(f"{OUTPUT}/{f}")
    for f in os.listdir(OUTPUT) if f.endswith(".csv")
)
print("\n" + "=" * 60)
print("STAR SCHEMA CREATED")
print("=" * 60)
print(f"\nFolder: {OUTPUT}/")
print(f"Total size: {total_size/1024/1024:.0f} MB")
print(f"\nFiles:")
for f in sorted(os.listdir(OUTPUT)):
    size = os.path.getsize(f"{OUTPUT}/{f}")
    print(f"  {f:30s} {size/1024/1024:8.1f} MB")
print(f"""
RELATIONSHIP MODEL IN POWER BI:
  fato_rais.cod_municipio     -> dim_municipio.cod_municipio
  fato_rais.cod_cnae_classe   -> dim_cnae.cod_cnae_classe
  fato_rais.cod_sexo          -> dim_sexo.cod_sexo
  fato_rais.cod_raca          -> dim_raca.cod_raca
  fato_rais.cod_faixa_etaria  -> dim_faixa_etaria.cod_faixa_etaria
  fato_rais.cod_escolaridade  -> dim_escolaridade.cod_escolaridade
""")
