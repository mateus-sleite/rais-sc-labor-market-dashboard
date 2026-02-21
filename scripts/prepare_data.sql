-- ============================================================
-- RAIS data preparation for Power BI
-- Technical Challenge - Data Analyst
-- SQL Server / T-SQL
-- ============================================================


-- ============================================================
-- 1. RAW TABLE IMPORT (staging)
-- ============================================================

-- Raw RAIS table (loaded via BULK INSERT or import wizard)
CREATE TABLE stg_rais (
    mun_trab            INT,
    ano                 INT,
    mes_admissao        INT,
    mes_desligamento    VARCHAR(10),
    vinculo_ativo_31_12 INT,
    vl_remun_media_nom  DECIMAL(12,2),
    cnae_2_0_classe     INT,
    sexo_trabalhador    INT,
    raca_cor            INT,
    tempo_emprego       VARCHAR(20),
    escolaridade_apos_2005 INT,
    faixa_etaria        INT
);

-- Load the 3 files into the same staging table
BULK INSERT stg_rais FROM 'rais_2020.csv' WITH (FIRSTROW = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '\n', CODEPAGE = '65001');
BULK INSERT stg_rais FROM 'rais_2021.csv' WITH (FIRSTROW = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '\n', CODEPAGE = '65001');
BULK INSERT stg_rais FROM 'rais_2022.csv' WITH (FIRSTROW = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '\n', CODEPAGE = '65001');


-- ============================================================
-- 2. RAW DATA VALIDATION
-- ============================================================

-- 2.1 Volume by year
SELECT ano, COUNT(*) AS total_registros
FROM stg_rais
GROUP BY ano
ORDER BY ano;
-- Expected: 2020=2,183,080 | 2021=2,472,398 | 2022=3,746,480

-- 2.2 Check null values by column
SELECT
    COUNT(*) AS total_registros,
    SUM(CASE WHEN mun_trab IS NULL THEN 1 ELSE 0 END)            AS nulos_mun_trab,
    SUM(CASE WHEN ano IS NULL THEN 1 ELSE 0 END)                 AS nulos_ano,
    SUM(CASE WHEN vinculo_ativo_31_12 IS NULL THEN 1 ELSE 0 END) AS nulos_vinculo,
    SUM(CASE WHEN vl_remun_media_nom IS NULL THEN 1 ELSE 0 END)  AS nulos_remuneracao,
    SUM(CASE WHEN cnae_2_0_classe IS NULL THEN 1 ELSE 0 END)     AS nulos_cnae,
    SUM(CASE WHEN sexo_trabalhador IS NULL THEN 1 ELSE 0 END)    AS nulos_sexo,
    SUM(CASE WHEN raca_cor IS NULL THEN 1 ELSE 0 END)            AS nulos_raca,
    SUM(CASE WHEN faixa_etaria IS NULL THEN 1 ELSE 0 END)        AS nulos_faixa_etaria,
    SUM(CASE WHEN escolaridade_apos_2005 IS NULL THEN 1 ELSE 0 END) AS nulos_escolaridade,
    SUM(CASE WHEN tempo_emprego IS NULL OR LTRIM(RTRIM(tempo_emprego)) = '' THEN 1 ELSE 0 END) AS nulos_tempo_emprego,
    SUM(CASE WHEN mes_desligamento IS NULL OR mes_desligamento LIKE '%{%' THEN 1 ELSE 0 END)   AS nulos_mes_deslig
FROM stg_rais;

-- 2.3 Check distribution of categorical codes
-- Gender (expected: 1=Male, 2=Female; also found 9=Not reported)
SELECT sexo_trabalhador, COUNT(*) AS qtd
FROM stg_rais
GROUP BY sexo_trabalhador
ORDER BY sexo_trabalhador;

-- Race/Color (expected: 1,2,4,6,8,9; also found 99=Not reported)
SELECT raca_cor, COUNT(*) AS qtd
FROM stg_rais
GROUP BY raca_cor
ORDER BY raca_cor;

-- Age Group (expected: 1 to 8; also found 99=Not classified)
SELECT faixa_etaria, COUNT(*) AS qtd
FROM stg_rais
GROUP BY faixa_etaria
ORDER BY faixa_etaria;

-- Education Level (expected: 1 to 11; also found 99=Not classified)
SELECT escolaridade_apos_2005, COUNT(*) AS qtd
FROM stg_rais
GROUP BY escolaridade_apos_2005
ORDER BY escolaridade_apos_2005;

-- 2.4 Remuneration analysis — outliers and zeros
SELECT
    COUNT(*)                                             AS total,
    SUM(CASE WHEN vl_remun_media_nom = 0 THEN 1 ELSE 0 END)    AS zeros,
    SUM(CASE WHEN vl_remun_media_nom < 0 THEN 1 ELSE 0 END)    AS negativos,
    SUM(CASE WHEN vl_remun_media_nom > 100000 THEN 1 ELSE 0 END) AS acima_100k,
    MIN(vl_remun_media_nom)                              AS minimo,
    ROUND(AVG(vl_remun_media_nom), 2)                    AS media,
    MAX(vl_remun_media_nom)                              AS maximo
FROM stg_rais;
-- Result: 531K zeros (6.3%), 0 negatives, 3,743 above 100k
-- Decision: keep zeros (apprentices/interns) and outliers (official data)

-- 2.5 Profile of records with remuneration = 0
SELECT
    vinculo_ativo_31_12,
    COUNT(*) AS qtd
FROM stg_rais
WHERE vl_remun_media_nom = 0
GROUP BY vinculo_ativo_31_12;
-- Result: ~50% active, ~50% inactive
-- Justification for keeping: apprentices, interns, quickly terminated records

-- 2.6 Top 10 highest remunerations (check plausibility)
SELECT TOP 10
    ano, mun_trab, vl_remun_media_nom, cnae_2_0_classe
FROM stg_rais
ORDER BY vl_remun_media_nom DESC;
-- Result: values up to R$ 2.95 million (0.04% of total)
-- Justification for keeping: official RAIS data, senior executives

-- 2.7 Check duplicates
SELECT
    COUNT(*) AS total_registros,
    COUNT(*) - COUNT(DISTINCT
        CONCAT(mun_trab, '|', ano, '|', mes_admissao, '|', mes_desligamento, '|',
               vinculo_ativo_31_12, '|', vl_remun_media_nom, '|', cnae_2_0_classe, '|',
               sexo_trabalhador, '|', raca_cor, '|', tempo_emprego, '|',
               escolaridade_apos_2005, '|', faixa_etaria)
    ) AS duplicatas_estimadas
FROM stg_rais;

-- Exact duplicate count using ROW_NUMBER
SELECT COUNT(*) AS total_duplicatas
FROM (
    SELECT
        ROW_NUMBER() OVER (
            PARTITION BY mun_trab, ano, mes_admissao, mes_desligamento,
                         vinculo_ativo_31_12, vl_remun_media_nom, cnae_2_0_classe,
                         sexo_trabalhador, raca_cor, tempo_emprego,
                         escolaridade_apos_2005, faixa_etaria
            ORDER BY (SELECT NULL)
        ) AS rn
    FROM stg_rais
) sub
WHERE rn > 1;
-- Result: 144,935 duplicates (1.7%)

-- 2.8 Duplicate distribution by year
SELECT ano, COUNT(*) AS duplicatas
FROM (
    SELECT
        ano,
        ROW_NUMBER() OVER (
            PARTITION BY mun_trab, ano, mes_admissao, mes_desligamento,
                         vinculo_ativo_31_12, vl_remun_media_nom, cnae_2_0_classe,
                         sexo_trabalhador, raca_cor, tempo_emprego,
                         escolaridade_apos_2005, faixa_etaria
            ORDER BY (SELECT NULL)
        ) AS rn
    FROM stg_rais
) sub
WHERE rn > 1
GROUP BY ano
ORDER BY ano;
-- Result: 2020=64K, 2021=78K, 2022=66K

-- 2.9 Employment tenure — check conversion
SELECT TOP 10 tempo_emprego,
    TRY_CAST(REPLACE(LTRIM(RTRIM(tempo_emprego)), ',', '.') AS DECIMAL(10,1)) AS convertido
FROM stg_rais
WHERE tempo_emprego IS NOT NULL;

-- 2.10 Check referential integrity with municipality
SELECT COUNT(*) AS municipios_sem_match
FROM (
    SELECT DISTINCT mun_trab FROM stg_rais
) r
LEFT JOIN (
    SELECT cod_municipio_completo / 10 AS cod_municipio
    FROM municipio_regiao_bruta
    WHERE uf = 42
) m ON r.mun_trab = m.cod_municipio
WHERE m.cod_municipio IS NULL;
-- Result: 0 municipalities without match


-- ============================================================
-- 3. DATA CORRECTION — Duplicate removal
-- ============================================================

-- Create clean staging table (without duplicates)
SELECT DISTINCT *
INTO stg_rais_limpa
FROM stg_rais;

-- Verify removal
SELECT
    (SELECT COUNT(*) FROM stg_rais) AS antes,
    (SELECT COUNT(*) FROM stg_rais_limpa) AS depois,
    (SELECT COUNT(*) FROM stg_rais) - (SELECT COUNT(*) FROM stg_rais_limpa) AS removidas;
-- Expected: 8,401,958 -> 8,257,023 (144,935 removed)

-- Replace original staging with clean one
DROP TABLE stg_rais;
EXEC sp_rename 'stg_rais_limpa', 'stg_rais';


-- ============================================================
-- 4. DIMENSION TABLES
-- ============================================================

-- Municipality/Region Dimension (source: municipio_regiao.ods, filtered for SC)
CREATE TABLE dim_municipio (
    cod_municipio           INT PRIMARY KEY,
    municipio               VARCHAR(100),
    regiao_imediata         VARCHAR(100),
    regiao_intermediaria    VARCHAR(100)
);

INSERT INTO dim_municipio
SELECT
    cod_municipio_completo / 10 AS cod_municipio,
    nome_municipio              AS municipio,
    nome_regiao_imediata        AS regiao_imediata,
    nome_regiao_intermediaria   AS regiao_intermediaria
FROM municipio_regiao_bruta
WHERE uf = 42;


-- CNAE Dimension (source: cnae.csv, deduplicated by class)
CREATE TABLE dim_cnae (
    cod_cnae_classe     INT PRIMARY KEY,
    cnae_classe         VARCHAR(200),
    cod_cnae_divisao    INT,
    cnae_divisao        VARCHAR(200)
);

INSERT INTO dim_cnae
SELECT DISTINCT
    CAST(REPLACE(REPLACE(classe, '.', ''), '-', '') AS INT) AS cod_cnae_classe,
    denominacao_classe  AS cnae_classe,
    CAST(divisao AS INT) AS cod_cnae_divisao,
    denominacao_divisao AS cnae_divisao
FROM cnae_bruta;


-- Gender Dimension (includes code 9 found in validation)
CREATE TABLE dim_sexo (
    cod_sexo    INT PRIMARY KEY,
    sexo        VARCHAR(20)
);

INSERT INTO dim_sexo VALUES
    (1, 'Masculino'),
    (2, 'Feminino'),
    (9, 'Não informado');  -- 5 records in the database


-- Race/Color Dimension (includes code 99 found in validation)
CREATE TABLE dim_raca (
    cod_raca    INT PRIMARY KEY,
    raca        VARCHAR(30)
);

INSERT INTO dim_raca VALUES
    (1, 'Indígena'),
    (2, 'Branca'),
    (4, 'Preta'),
    (6, 'Amarela'),
    (8, 'Parda'),
    (9, 'Não identificado'),
    (99, 'Não informado');  -- 612,115 records (7.4%)


-- Age Group Dimension (includes code 99 found in validation)
CREATE TABLE dim_faixa_etaria (
    cod_faixa_etaria    INT PRIMARY KEY,
    faixa_etaria        VARCHAR(30)
);

INSERT INTO dim_faixa_etaria VALUES
    (1, '10 a 14 anos'),
    (2, '15 a 17 anos'),
    (3, '18 a 24 anos'),
    (4, '25 a 29 anos'),
    (5, '30 a 39 anos'),
    (6, '40 a 49 anos'),
    (7, '50 a 64 anos'),
    (8, '65 anos ou mais'),
    (99, 'Não classificado');  -- 1 record


-- Education Level Dimension (includes code 99 found in validation)
CREATE TABLE dim_escolaridade (
    cod_escolaridade    INT PRIMARY KEY,
    escolaridade        VARCHAR(30)
);

INSERT INTO dim_escolaridade VALUES
    (1,  'Analfabeto'),
    (2,  'Até 5ª Incompleto'),
    (3,  '5ª Completo'),
    (4,  '6ª a 9ª Incompleto'),
    (5,  '9ª Completo'),
    (6,  'Médio Incompleto'),
    (7,  'Médio Completo'),
    (8,  'Superior Incompleto'),
    (9,  'Superior Completo'),
    (10, 'Mestrado'),
    (11, 'Doutorado'),
    (99, 'Não classificado');  -- 5 records


-- ============================================================
-- 5. FACT TABLE
-- ============================================================

CREATE TABLE fato_rais (
    ano                     INT,
    cod_municipio           INT,
    vinculo_ativo           INT,
    remuneracao_media       DECIMAL(12,2),
    cod_cnae_classe         INT,
    cod_cnae_divisao        INT,
    cod_sexo                INT,
    cod_raca                INT,
    cod_faixa_etaria        INT,
    cod_escolaridade        INT,
    tempo_emprego_meses     DECIMAL(10,1),
    mes_admissao            INT,
    mes_desligamento        INT,

    FOREIGN KEY (cod_municipio)    REFERENCES dim_municipio(cod_municipio),
    FOREIGN KEY (cod_cnae_classe)  REFERENCES dim_cnae(cod_cnae_classe),
    FOREIGN KEY (cod_sexo)         REFERENCES dim_sexo(cod_sexo),
    FOREIGN KEY (cod_raca)         REFERENCES dim_raca(cod_raca),
    FOREIGN KEY (cod_faixa_etaria) REFERENCES dim_faixa_etaria(cod_faixa_etaria),
    FOREIGN KEY (cod_escolaridade) REFERENCES dim_escolaridade(cod_escolaridade)
);

INSERT INTO fato_rais
SELECT
    s.ano,
    s.mun_trab                  AS cod_municipio,
    s.vinculo_ativo_31_12       AS vinculo_ativo,
    s.vl_remun_media_nom        AS remuneracao_media,
    s.cnae_2_0_classe           AS cod_cnae_classe,
    c.cod_cnae_divisao,
    s.sexo_trabalhador          AS cod_sexo,
    s.raca_cor                  AS cod_raca,
    s.faixa_etaria              AS cod_faixa_etaria,
    s.escolaridade_apos_2005    AS cod_escolaridade,
    TRY_CAST(
        REPLACE(LTRIM(RTRIM(s.tempo_emprego)), ',', '.')
        AS DECIMAL(10,1)
    )                           AS tempo_emprego_meses,
    s.mes_admissao,
    CASE
        WHEN s.mes_desligamento LIKE '%{%' THEN NULL
        ELSE TRY_CAST(s.mes_desligamento AS INT)
    END                         AS mes_desligamento
FROM stg_rais s
LEFT JOIN dim_cnae c ON s.cnae_2_0_classe = c.cod_cnae_classe;


-- ============================================================
-- 6. INDEXES FOR PERFORMANCE
-- ============================================================

CREATE INDEX idx_fato_ano            ON fato_rais (ano);
CREATE INDEX idx_fato_municipio      ON fato_rais (cod_municipio);
CREATE INDEX idx_fato_cnae           ON fato_rais (cod_cnae_classe);
CREATE INDEX idx_fato_vinculo        ON fato_rais (vinculo_ativo);
CREATE INDEX idx_fato_sexo           ON fato_rais (cod_sexo);
CREATE INDEX idx_fato_raca           ON fato_rais (cod_raca);


-- ============================================================
-- 7. POST-LOAD VALIDATION
-- ============================================================

-- 7.1 Final count
SELECT COUNT(*) AS total_fato FROM fato_rais;
-- Expected: 8,257,023

-- 7.2 Records by year
SELECT ano, COUNT(*) AS total_vinculos
FROM fato_rais
GROUP BY ano
ORDER BY ano;

-- 7.3 Referential integrity — check orphan records
SELECT 'municipio' AS dimensao, COUNT(*) AS orfaos
FROM fato_rais f
LEFT JOIN dim_municipio m ON f.cod_municipio = m.cod_municipio
WHERE m.cod_municipio IS NULL
UNION ALL
SELECT 'cnae', COUNT(*)
FROM fato_rais f
LEFT JOIN dim_cnae c ON f.cod_cnae_classe = c.cod_cnae_classe
WHERE c.cod_cnae_classe IS NULL
UNION ALL
SELECT 'sexo', COUNT(*)
FROM fato_rais f
LEFT JOIN dim_sexo s ON f.cod_sexo = s.cod_sexo
WHERE s.cod_sexo IS NULL
UNION ALL
SELECT 'raca', COUNT(*)
FROM fato_rais f
LEFT JOIN dim_raca r ON f.cod_raca = r.cod_raca
WHERE r.cod_raca IS NULL
UNION ALL
SELECT 'faixa_etaria', COUNT(*)
FROM fato_rais f
LEFT JOIN dim_faixa_etaria fe ON f.cod_faixa_etaria = fe.cod_faixa_etaria
WHERE fe.cod_faixa_etaria IS NULL
UNION ALL
SELECT 'escolaridade', COUNT(*)
FROM fato_rais f
LEFT JOIN dim_escolaridade e ON f.cod_escolaridade = e.cod_escolaridade
WHERE e.cod_escolaridade IS NULL;
-- Expected: all with 0 orphans

-- 7.4 Check remuneration in final table
SELECT
    COUNT(*)                                                        AS total,
    SUM(CASE WHEN remuneracao_media = 0 THEN 1 ELSE 0 END)         AS zeros,
    SUM(CASE WHEN remuneracao_media < 0 THEN 1 ELSE 0 END)         AS negativos,
    ROUND(AVG(CASE WHEN vinculo_ativo = 1 AND remuneracao_media > 0
              THEN remuneracao_media END), 2)                       AS media_ativos,
    COUNT(DISTINCT cod_municipio)                                   AS municipios,
    COUNT(DISTINCT cod_cnae_classe)                                 AS setores_cnae
FROM fato_rais;
-- Expected: media_ativos ~R$ 3,450, 295 municipalities, ~639 sectors

-- 7.5 General model overview
SELECT
    (SELECT COUNT(*) FROM fato_rais)         AS registros_fato,
    (SELECT COUNT(*) FROM dim_municipio)     AS municipios,
    (SELECT COUNT(*) FROM dim_cnae)          AS setores_cnae,
    (SELECT COUNT(*) FROM dim_sexo)          AS categorias_sexo,
    (SELECT COUNT(*) FROM dim_raca)          AS categorias_raca,
    (SELECT COUNT(*) FROM dim_faixa_etaria)  AS faixas_etarias,
    (SELECT COUNT(*) FROM dim_escolaridade)  AS niveis_escolaridade;


-- ============================================================
-- 8. ANALYTICAL QUERIES (dashboard indicator validation)
-- ============================================================

-- 8.1 Active employment records by intermediate region
SELECT
    m.regiao_intermediaria,
    f.ano,
    COUNT(*) AS vinculos_ativos
FROM fato_rais f
JOIN dim_municipio m ON f.cod_municipio = m.cod_municipio
WHERE f.vinculo_ativo = 1
GROUP BY m.regiao_intermediaria, f.ano
ORDER BY m.regiao_intermediaria, f.ano;

-- 8.2 Average remuneration by CNAE division (Top 10)
SELECT TOP 10
    c.cnae_divisao,
    ROUND(AVG(f.remuneracao_media), 2) AS media_remuneracao,
    COUNT(*) AS vinculos_ativos
FROM fato_rais f
JOIN dim_cnae c ON f.cod_cnae_classe = c.cod_cnae_classe
WHERE f.vinculo_ativo = 1 AND f.remuneracao_media > 0
GROUP BY c.cnae_divisao
ORDER BY media_remuneracao DESC;

-- 8.3 Gender wage disparity by region
SELECT
    m.regiao_intermediaria,
    ROUND(AVG(CASE WHEN f.cod_sexo = 1 THEN f.remuneracao_media END), 2) AS media_masculino,
    ROUND(AVG(CASE WHEN f.cod_sexo = 2 THEN f.remuneracao_media END), 2) AS media_feminino,
    ROUND(
        (AVG(CASE WHEN f.cod_sexo = 1 THEN f.remuneracao_media END) -
         AVG(CASE WHEN f.cod_sexo = 2 THEN f.remuneracao_media END)) /
        NULLIF(AVG(CASE WHEN f.cod_sexo = 1 THEN f.remuneracao_media END), 0) * 100
    , 2) AS gap_genero_pct
FROM fato_rais f
JOIN dim_municipio m ON f.cod_municipio = m.cod_municipio
WHERE f.vinculo_ativo = 1 AND f.remuneracao_media > 0
GROUP BY m.regiao_intermediaria
ORDER BY gap_genero_pct DESC;

-- 8.4 Racial wage disparity by region
SELECT
    m.regiao_intermediaria,
    ROUND(AVG(CASE WHEN f.cod_raca = 2 THEN f.remuneracao_media END), 2) AS media_branca,
    ROUND(AVG(CASE WHEN f.cod_raca = 4 THEN f.remuneracao_media END), 2) AS media_preta,
    ROUND(
        (AVG(CASE WHEN f.cod_raca = 2 THEN f.remuneracao_media END) -
         AVG(CASE WHEN f.cod_raca = 4 THEN f.remuneracao_media END)) /
        NULLIF(AVG(CASE WHEN f.cod_raca = 2 THEN f.remuneracao_media END), 0) * 100
    , 2) AS gap_racial_pct
FROM fato_rais f
JOIN dim_municipio m ON f.cod_municipio = m.cod_municipio
WHERE f.vinculo_ativo = 1 AND f.remuneracao_media > 0
GROUP BY m.regiao_intermediaria
ORDER BY gap_racial_pct DESC;

-- 8.5 Gender wage gap by education level
SELECT
    e.escolaridade,
    ROUND(AVG(CASE WHEN f.cod_sexo = 1 THEN f.remuneracao_media END), 2) AS media_masculino,
    ROUND(AVG(CASE WHEN f.cod_sexo = 2 THEN f.remuneracao_media END), 2) AS media_feminino,
    ROUND(
        (AVG(CASE WHEN f.cod_sexo = 1 THEN f.remuneracao_media END) -
         AVG(CASE WHEN f.cod_sexo = 2 THEN f.remuneracao_media END)) /
        NULLIF(AVG(CASE WHEN f.cod_sexo = 1 THEN f.remuneracao_media END), 0) * 100
    , 2) AS gap_genero_pct
FROM fato_rais f
JOIN dim_escolaridade e ON f.cod_escolaridade = e.cod_escolaridade
WHERE f.vinculo_ativo = 1 AND f.remuneracao_media > 0
GROUP BY e.escolaridade
ORDER BY gap_genero_pct DESC;

-- 8.6 Female participation by sector (Top 10 sectors by volume)
SELECT TOP 10
    c.cnae_divisao,
    COUNT(*) AS vinculos_ativos,
    ROUND(
        CAST(SUM(CASE WHEN f.cod_sexo = 2 THEN 1 ELSE 0 END) AS FLOAT) /
        NULLIF(COUNT(*), 0) * 100
    , 2) AS participacao_feminina_pct
FROM fato_rais f
JOIN dim_cnae c ON f.cod_cnae_classe = c.cod_cnae_classe
WHERE f.vinculo_ativo = 1
GROUP BY c.cnae_divisao
ORDER BY vinculos_ativos DESC;


-- ============================================================
-- 9. CLEANUP
-- ============================================================

-- Remove staging table after full load
DROP TABLE IF EXISTS stg_rais;
