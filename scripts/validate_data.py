"""
Validação de integridade dos dados RAIS tratados
"""
import pandas as pd
import numpy as np

PBI = "C:/Users/Mateus/Business Intelligence/projetos/desafio-analista-dados/dados_pbi"

print("Carregando dados...")
fato = pd.read_csv(f"{PBI}/fato_rais.csv", low_memory=False)
dim_mun = pd.read_csv(f"{PBI}/dim_municipio.csv")
dim_cnae = pd.read_csv(f"{PBI}/dim_cnae.csv")

print(f"Fato: {len(fato):,} linhas\n")

# ============================================================
# 1. VALORES NULOS POR COLUNA
# ============================================================
print("=" * 60)
print("1. VALORES NULOS")
print("=" * 60)
nulls = fato.isnull().sum()
for col in fato.columns:
    n = nulls[col]
    pct = n / len(fato) * 100
    status = f"  {n:>10,} ({pct:.2f}%)" if n > 0 else "  OK"
    print(f"  {col:30s}{status}")

# ============================================================
# 2. VALORES FORA DO ESPERADO (outliers / códigos inválidos)
# ============================================================
print("\n" + "=" * 60)
print("2. VALORES ÚNICOS E DISTRIBUIÇÃO")
print("=" * 60)

print("\n--- ano ---")
print(fato["ano"].value_counts().sort_index().to_string())

print("\n--- vinculo_ativo ---")
print(fato["vinculo_ativo"].value_counts().sort_index().to_string())

print("\n--- cod_sexo ---")
print(fato["cod_sexo"].value_counts().sort_index().to_string())

print("\n--- cod_raca ---")
print(fato["cod_raca"].value_counts().sort_index().to_string())

print("\n--- cod_faixa_etaria ---")
print(fato["cod_faixa_etaria"].value_counts().sort_index().to_string())

print("\n--- cod_escolaridade ---")
print(fato["cod_escolaridade"].value_counts().sort_index().to_string())

print("\n--- mes_admissao ---")
print(fato["mes_admissao"].value_counts().sort_index().to_string())

print("\n--- mes_desligamento (top 15) ---")
print(fato["mes_desligamento"].value_counts(dropna=False).head(15).to_string())

# ============================================================
# 3. REMUNERAÇÃO - OUTLIERS
# ============================================================
print("\n" + "=" * 60)
print("3. REMUNERAÇÃO MÉDIA")
print("=" * 60)
rem = fato["remuneracao_media"]
print(f"  Min:      {rem.min():>12,.2f}")
print(f"  Q1:       {rem.quantile(0.25):>12,.2f}")
print(f"  Mediana:  {rem.quantile(0.50):>12,.2f}")
print(f"  Média:    {rem.mean():>12,.2f}")
print(f"  Q3:       {rem.quantile(0.75):>12,.2f}")
print(f"  Max:      {rem.max():>12,.2f}")
print(f"  Zeros:    {(rem == 0).sum():,}")
print(f"  Negativos:{(rem < 0).sum():,}")
print(f"  Nulos:    {rem.isnull().sum():,}")
print(f"  > 100k:   {(rem > 100000).sum():,}")

# ============================================================
# 4. TEMPO DE EMPREGO
# ============================================================
print("\n" + "=" * 60)
print("4. TEMPO DE EMPREGO (meses)")
print("=" * 60)
te = fato["tempo_emprego_meses"]
print(f"  Min:      {te.min():>10,.1f}")
print(f"  Mediana:  {te.quantile(0.50):>10,.1f}")
print(f"  Média:    {te.mean():>10,.1f}")
print(f"  Max:      {te.max():>10,.1f}")
print(f"  Negativos:{(te < 0).sum():,}")
print(f"  Nulos:    {te.isnull().sum():,}")

# ============================================================
# 5. INTEGRIDADE REFERENCIAL (FK match)
# ============================================================
print("\n" + "=" * 60)
print("5. INTEGRIDADE REFERENCIAL")
print("=" * 60)

# Município
mun_fato = set(fato["cod_municipio"].dropna().unique())
mun_dim = set(dim_mun["cod_municipio"].unique())
orphans_mun = mun_fato - mun_dim
print(f"  Municípios na fato sem match na dimensão: {len(orphans_mun)}")
if orphans_mun:
    print(f"    Códigos órfãos: {sorted(orphans_mun)[:20]}")

# CNAE
cnae_fato = set(fato["cod_cnae_classe"].dropna().unique())
cnae_dim = set(dim_cnae["cod_cnae_classe"].unique())
orphans_cnae = cnae_fato - cnae_dim
print(f"  CNAEs na fato sem match na dimensão: {len(orphans_cnae)}")
if orphans_cnae:
    # Contar registros afetados
    n_orphan = fato[fato["cod_cnae_classe"].isin(orphans_cnae)].shape[0]
    print(f"    Códigos órfãos: {sorted(orphans_cnae)[:20]}")
    print(f"    Registros afetados: {n_orphan:,}")

# Códigos válidos
valid_sexo = {1, 2}
valid_raca = {1, 2, 4, 6, 8, 9}
valid_faixa = {1, 2, 3, 4, 5, 6, 7, 8}
valid_esc = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11}

for col, valid, name in [
    ("cod_sexo", valid_sexo, "Sexo"),
    ("cod_raca", valid_raca, "Raça"),
    ("cod_faixa_etaria", valid_faixa, "Faixa etária"),
    ("cod_escolaridade", valid_esc, "Escolaridade"),
]:
    vals = set(fato[col].dropna().unique())
    invalid = vals - valid
    if invalid:
        n_invalid = fato[fato[col].isin(invalid)].shape[0]
        print(f"  {name} - valores inválidos: {invalid} ({n_invalid:,} registros)")
    else:
        print(f"  {name} - OK")

# ============================================================
# 6. DUPLICATAS
# ============================================================
print("\n" + "=" * 60)
print("6. DUPLICATAS")
print("=" * 60)
dupes = fato.duplicated().sum()
print(f"  Linhas 100% duplicadas: {dupes:,} ({dupes/len(fato)*100:.2f}%)")

print("\n" + "=" * 60)
print("VALIDAÇÃO CONCLUÍDA")
print("=" * 60)
