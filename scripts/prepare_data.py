"""
RAIS data preparation for Power BI
Technical Challenge - Data Analyst
"""
import pandas as pd
import os
import time

BASE = "C:/Users/Mateus/Business Intelligence/projetos/desafio-analista-dados/Bases/Bases"
OUTPUT = "C:/Users/Mateus/Business Intelligence/projetos/desafio-analista-dados/dados_tratados"
os.makedirs(OUTPUT, exist_ok=True)

# ============================================================
# 1. AUXILIARY TABLES
# ============================================================
print("=" * 60)
print("1. Loading auxiliary tables...")
print("=" * 60)

# --- Municipality/Region ---
print("  -> municipio_regiao.ods")
mun = pd.read_excel(f"{BASE}/municipio_regiao.ods", engine="odf", skiprows=6)
mun.columns = [
    "uf", "nome_uf",
    "regiao_intermediaria", "nome_regiao_intermediaria",
    "regiao_imediata", "nome_regiao_imediata",
    "municipio", "cod_municipio_completo", "nome_municipio", "extra"
]
mun = mun.drop(columns=["extra"])
# Filter SC (UF=42)
mun_sc = mun[mun["uf"] == 42].copy()
# Create 6-digit code to match with RAIS
mun_sc["mun_trab"] = mun_sc["cod_municipio_completo"] // 10
mun_sc = mun_sc[["mun_trab", "nome_municipio", "regiao_imediata",
                  "nome_regiao_imediata", "regiao_intermediaria",
                  "nome_regiao_intermediaria"]].drop_duplicates()
print(f"     {len(mun_sc)} SC municipalities")

# --- CNAE ---
print("  -> cnae.csv")
cnae = pd.read_csv(f"{BASE}/cnae.csv", encoding="latin-1")
# Create numeric code to match with RAIS
cnae["cnae_2_0_classe"] = cnae["Classe"].str.replace(r"[.\-]", "", regex=True).astype(int)
# Get only class and division (without duplicates)
cnae_classe = cnae[["cnae_2_0_classe", "denominacao_classe",
                     "divisao", "denominacao_divisao"]].drop_duplicates(
    subset=["cnae_2_0_classe"]
)
print(f"     {len(cnae_classe)} CNAE classes")

# --- Decoding dictionaries ---
print("  -> Creating decoding dictionaries")

dict_sexo = {1: "Masculino", 2: "Feminino"}

dict_raca_cor = {
    1: "Indígena", 2: "Branca", 4: "Preta",
    6: "Amarela", 8: "Parda", 9: "Não identificado"
}

dict_faixa_etaria = {
    1: "10 a 14 anos", 2: "15 a 17 anos", 3: "18 a 24 anos",
    4: "25 a 29 anos", 5: "30 a 39 anos", 6: "40 a 49 anos",
    7: "50 a 64 anos", 8: "65 anos ou mais"
}

dict_escolaridade = {
    1: "Analfabeto", 2: "Até 5ª Incompleto", 3: "5ª Completo",
    4: "6ª a 9ª Incompleto", 5: "9ª Completo", 6: "Médio Incompleto",
    7: "Médio Completo", 8: "Superior Incompleto", 9: "Superior Completo",
    10: "Mestrado", 11: "Doutorado"
}

dict_vinculo = {0: "Inativo", 1: "Ativo"}

# ============================================================
# 2. LOAD AND PROCESS RAIS
# ============================================================
print("\n" + "=" * 60)
print("2. Loading and processing RAIS 2020-2022...")
print("=" * 60)

dfs = []
for ano in [2020, 2021, 2022]:
    t0 = time.time()
    print(f"\n  -> rais_{ano}.csv", end="", flush=True)
    df = pd.read_csv(f"{BASE}/rais_{ano}.csv")
    print(f" ({len(df):,} rows, {time.time()-t0:.1f}s)")

    # Strip whitespace from object columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    dfs.append(df)

rais = pd.concat(dfs, ignore_index=True)
del dfs
print(f"\n  Combined total: {len(rais):,} rows")

# ============================================================
# 3. JOINS AND DECODINGS
# ============================================================
print("\n" + "=" * 60)
print("3. Applying joins and decodings...")
print("=" * 60)

# Municipality/region join
print("  -> Municipality/region join")
rais = rais.merge(mun_sc, on="mun_trab", how="left")

# CNAE join
print("  -> CNAE join")
rais = rais.merge(cnae_classe, on="cnae_2_0_classe", how="left")

# Decode fields
print("  -> Decoding categorical fields")
rais["sexo"] = rais["sexo_trabalhador"].map(dict_sexo)
rais["raca"] = rais["raca_cor"].map(dict_raca_cor)
rais["faixa_etaria_desc"] = rais["faixa_etaria"].map(dict_faixa_etaria)
rais["escolaridade"] = rais["escolaridade_apos_2005"].map(dict_escolaridade)
rais["vinculo_status"] = rais["vinculo_ativo_31_12"].map(dict_vinculo)

# Process tempo_emprego (comes with comma as decimal)
print("  -> Processing tempo_emprego")
rais["tempo_emprego"] = (
    rais["tempo_emprego"]
    .astype(str)
    .str.strip()
    .str.replace(",", ".", regex=False)
)
rais["tempo_emprego"] = pd.to_numeric(rais["tempo_emprego"], errors="coerce")

# Process mes_desligamento
rais["mes_desligamento"] = rais["mes_desligamento"].astype(str).str.strip()
rais.loc[rais["mes_desligamento"].str.contains("{", na=False), "mes_desligamento"] = None
rais["mes_desligamento"] = pd.to_numeric(rais["mes_desligamento"], errors="coerce")

# ============================================================
# 4. SELECT AND RENAME FINAL COLUMNS
# ============================================================
print("\n" + "=" * 60)
print("4. Organizing final columns...")
print("=" * 60)

colunas_finais = {
    "ano": "ano",
    "mun_trab": "cod_municipio",
    "nome_municipio": "municipio",
    "nome_regiao_imediata": "regiao_imediata",
    "nome_regiao_intermediaria": "regiao_intermediaria",
    "vinculo_ativo_31_12": "vinculo_ativo",
    "vinculo_status": "vinculo_status",
    "vl_remun_media_nom": "remuneracao_media",
    "cnae_2_0_classe": "cod_cnae_classe",
    "denominacao_classe": "cnae_classe",
    "divisao": "cod_cnae_divisao",
    "denominacao_divisao": "cnae_divisao",
    "sexo_trabalhador": "cod_sexo",
    "sexo": "sexo",
    "raca_cor": "cod_raca",
    "raca": "raca",
    "faixa_etaria": "cod_faixa_etaria",
    "faixa_etaria_desc": "faixa_etaria",
    "escolaridade_apos_2005": "cod_escolaridade",
    "escolaridade": "escolaridade",
    "tempo_emprego": "tempo_emprego_meses",
    "mes_admissao": "mes_admissao",
    "mes_desligamento": "mes_desligamento",
}

rais_final = rais[list(colunas_finais.keys())].rename(columns=colunas_finais)

# ============================================================
# 5. OPTIMIZE DATA TYPES
# ============================================================
print("  -> Optimizing data types")

# Convert to categories (drastically reduces memory)
cat_cols = [
    "municipio", "regiao_imediata", "regiao_intermediaria",
    "vinculo_status", "cnae_classe", "cnae_divisao",
    "sexo", "raca", "faixa_etaria", "escolaridade"
]
for col in cat_cols:
    rais_final[col] = rais_final[col].astype("category")

# Smaller integers where possible
int_cols_8 = ["vinculo_ativo", "cod_sexo", "cod_raca", "cod_faixa_etaria", "cod_escolaridade"]
for col in int_cols_8:
    rais_final[col] = rais_final[col].astype("Int8")

rais_final["ano"] = rais_final["ano"].astype("Int16")
rais_final["cod_municipio"] = rais_final["cod_municipio"].astype("Int32")
rais_final["cod_cnae_classe"] = rais_final["cod_cnae_classe"].astype("Int32")
rais_final["cod_cnae_divisao"] = pd.to_numeric(rais_final["cod_cnae_divisao"], errors="coerce").astype("Int16")

# ============================================================
# 6. EXPORT
# ============================================================
print("\n" + "=" * 60)
print("5. Exporting treated data...")
print("=" * 60)

# CSV for Power BI
csv_path = f"{OUTPUT}/rais_tratada.csv"
print(f"  -> {csv_path}")
rais_final.to_csv(csv_path, index=False, encoding="utf-8-sig")

# Export municipality/region table separately (for maps)
mun_export = mun_sc.rename(columns={
    "mun_trab": "cod_municipio",
    "nome_municipio": "municipio",
    "nome_regiao_imediata": "regiao_imediata",
    "regiao_imediata": "cod_regiao_imediata",
    "nome_regiao_intermediaria": "regiao_intermediaria",
    "regiao_intermediaria": "cod_regiao_intermediaria"
})
mun_path = f"{OUTPUT}/dim_municipio_regiao.csv"
print(f"  -> {mun_path}")
mun_export.to_csv(mun_path, index=False, encoding="utf-8-sig")

# Export CNAE table separately
cnae_path = f"{OUTPUT}/dim_cnae.csv"
print(f"  -> {cnae_path}")
cnae_classe.rename(columns={
    "cnae_2_0_classe": "cod_cnae_classe",
    "denominacao_classe": "cnae_classe",
    "divisao": "cod_cnae_divisao",
    "denominacao_divisao": "cnae_divisao"
}).to_csv(cnae_path, index=False, encoding="utf-8-sig")

# ============================================================
# 7. SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Total rows: {len(rais_final):,}")
print(f"Columns: {len(rais_final.columns)}")
print(f"\nBy year:")
print(rais_final.groupby("ano").size().to_string())
print(f"\nMunicipalities: {rais_final['municipio'].nunique()}")
print(f"Immediate regions: {rais_final['regiao_imediata'].nunique()}")
print(f"Intermediate regions: {rais_final['regiao_intermediaria'].nunique()}")
print(f"\nFile size: {os.path.getsize(csv_path) / 1024 / 1024:.1f} MB")
print(f"\nFiles generated in: {OUTPUT}/")
print("  - rais_tratada.csv (main fact table)")
print("  - dim_municipio_regiao.csv (municipality dimension)")
print("  - dim_cnae.csv (sector dimension)")
print("\nDone! Open Power BI and import the files from the dados_tratados/ folder")
