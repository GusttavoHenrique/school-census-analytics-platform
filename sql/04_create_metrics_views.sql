CREATE SCHEMA IF NOT EXISTS analytics;

DROP VIEW IF EXISTS analytics.view_escolas_por_uf_dependencia;
CREATE VIEW analytics.view_escolas_por_uf_dependencia AS
SELECT
    e.ano_censo,
    e.sigla_uf,
    d.dependencia_administrativa,
    COUNT(DISTINCT e.id_escola) AS quantidade_escolas
FROM analytics.dim_escola e
LEFT JOIN analytics.dim_dependencia_administrativa d ON (e.id_dependencia_administrativa = d.id_dependencia_administrativa)
GROUP BY e.ano_censo, e.sigla_uf, d.dependencia_administrativa;


DROP VIEW IF EXISTS analytics.view_escolas_por_uf_localizacao;
CREATE VIEW analytics.view_escolas_por_uf_localizacao AS
SELECT
    e.ano_censo,
    e.sigla_uf,
    l.localizacao,
    COUNT(DISTINCT e.id_escola) AS quantidade_escolas
FROM analytics.dim_escola e
LEFT JOIN analytics.dim_localizacao l ON (e.id_localizacao = l.id_localizacao)
GROUP BY e.ano_censo, e.sigla_uf, l.localizacao;


DROP VIEW IF EXISTS analytics.view_percentual_escolas_infraestrutura;
CREATE VIEW analytics.view_percentual_escolas_infraestrutura AS
SELECT
    e.ano_censo,
    e.sigla_uf,
    COUNT(DISTINCT e.id_escola) AS quantidade_escolas,
    ROUND(100.0 * AVG(CASE WHEN e.possui_internet = '1' THEN 1 ELSE 0 END), 2) AS percentual_escolas_com_internet,
    ROUND(100.0 * AVG(CASE WHEN e.possui_biblioteca = '1' THEN 1 ELSE 0 END), 2) AS percentual_escolas_com_biblioteca,
    ROUND(100.0 * AVG(CASE WHEN e.possui_laboratorio_informatica = '1' THEN 1 ELSE 0 END), 2) AS percentual_escolas_com_laboratorio_informatica,
    ROUND(100.0 * AVG(CASE WHEN e.possui_laboratorio_ciencias = '1' THEN 1 ELSE 0 END), 2) AS percentual_escolas_com_laboratorio_ciencias,
    ROUND(100.0 * AVG(CASE WHEN e.possui_agua_potavel = '1' THEN 1 ELSE 0 END), 2) AS percentual_escolas_com_agua_potavel,
    ROUND(100.0 * AVG(CASE WHEN e.possui_energia_rede_publica = '1' THEN 1 ELSE 0 END), 2) AS percentual_escolas_com_energia_rede_publica
FROM analytics.dim_escola e
GROUP BY e.ano_censo, e.sigla_uf;


DROP VIEW IF EXISTS analytics.view_turmas_por_escola_uf;
CREATE VIEW analytics.view_turmas_por_escola_uf AS
SELECT
    e.ano_censo,
    e.sigla_uf,
    COUNT(*) AS quantidade_turmas,
    COUNT(DISTINCT e.id_escola) AS quantidade_escolas,
    ROUND(COUNT(*)::numeric / NULLIF(COUNT(DISTINCT e.id_escola), 0), 2) AS media_turmas_por_escola
FROM analytics.dim_turma t
JOIN analytics.dim_escola e ON (t.id_escola = e.id_escola AND t.ano_censo = e.ano_censo)
GROUP BY e.ano_censo, e.sigla_uf;


DROP VIEW IF EXISTS analytics.view_matriculas_por_uf_dependencia;
CREATE VIEW analytics.view_matriculas_por_uf_dependencia AS
SELECT
    e.ano_censo,
    e.sigla_uf,
    d.dependencia_administrativa,
    COUNT(*) AS quantidade_matriculas
FROM analytics.fato_matricula m
JOIN analytics.dim_escola e ON (m.id_escola = e.id_escola AND m.ano_censo = e.ano_censo)
LEFT JOIN analytics.dim_dependencia_administrativa d ON (e.id_dependencia_administrativa = d.id_dependencia_administrativa)
GROUP BY e.ano_censo, e.sigla_uf, d.dependencia_administrativa;


DROP VIEW IF EXISTS analytics.view_razao_alunos_por_turma;
CREATE VIEW analytics.view_razao_alunos_por_turma AS
WITH matriculas_por_uf AS (
    SELECT
        e.ano_censo,
        e.sigla_uf,
        COUNT(*) AS quantidade_matriculas
    FROM analytics.fato_matricula m
    JOIN analytics.dim_escola e ON (m.id_escola = e.id_escola AND m.ano_censo = e.ano_censo)
    GROUP BY e.ano_censo, e.sigla_uf
),
turmas_por_uf AS (
    SELECT
        e.ano_censo,
        e.sigla_uf,
        COUNT(*) AS quantidade_turmas
    FROM analytics.dim_turma t
    JOIN analytics.dim_escola e ON (t.id_escola = e.id_escola AND t.ano_censo = e.ano_censo)
    GROUP BY e.ano_censo, e.sigla_uf
)
SELECT
    m.ano_censo,
    m.sigla_uf,
    m.quantidade_matriculas,
    t.quantidade_turmas,
    ROUND(m.quantidade_matriculas::numeric / NULLIF(t.quantidade_turmas, 0), 2) AS razao_alunos_por_turma
FROM matriculas_por_uf m
JOIN turmas_por_uf t ON (m.ano_censo = t.ano_censo AND m.sigla_uf = t.sigla_uf);