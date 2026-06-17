CREATE SCHEMA IF NOT EXISTS analytics;

-- ============================================================================
-- View: view_escolas_por_uf_dependencia
--
-- Purpose:
--     Returns the number of schools grouped by census year,
--     state and administrative dependency.
-- ============================================================================
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

COMMENT ON VIEW analytics.view_escolas_por_uf_dependencia IS 'Number of schools grouped by census year, state and administrative dependency.';
COMMENT ON COLUMN analytics.view_escolas_por_uf_dependencia.ano_censo IS 'School Census reference year.';
COMMENT ON COLUMN analytics.view_escolas_por_uf_dependencia.sigla_uf IS 'Brazilian state abbreviation.';
COMMENT ON COLUMN analytics.view_escolas_por_uf_dependencia.dependencia_administrativa IS 'Administrative dependency classification (Federal, State, Municipal or Private).';
COMMENT ON COLUMN analytics.view_escolas_por_uf_dependencia.quantidade_escolas IS 'Total number of distinct schools.';

-- ============================================================================
-- View: view_escolas_por_uf_localizacao
--
-- Purpose:
--     Returns the number of schools grouped by census year,
--     state and geographic location.
-- ============================================================================
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

COMMENT ON VIEW analytics.view_escolas_por_uf_localizacao IS 'Number of schools grouped by census year, state and location.';
COMMENT ON COLUMN analytics.view_escolas_por_uf_localizacao.ano_censo IS 'School Census reference year.';
COMMENT ON COLUMN analytics.view_escolas_por_uf_localizacao.sigla_uf IS 'Brazilian state abbreviation.';
COMMENT ON COLUMN analytics.view_escolas_por_uf_localizacao.localizacao IS 'School location classification (Urban or Rural).';
COMMENT ON COLUMN analytics.view_escolas_por_uf_localizacao.quantidade_escolas IS 'Total number of distinct schools.';

-- ============================================================================
-- View: view_percentual_escolas_infraestrutura
--
-- Purpose:
--     Calculates infrastructure coverage indicators by census year
--     and state.
-- ============================================================================
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

COMMENT ON VIEW analytics.view_percentual_escolas_infraestrutura IS 'Infrastructure coverage indicators grouped by census year and state.';
COMMENT ON COLUMN analytics.view_percentual_escolas_infraestrutura.ano_censo IS 'School Census reference year.';
COMMENT ON COLUMN analytics.view_percentual_escolas_infraestrutura.sigla_uf IS 'Brazilian state abbreviation.';
COMMENT ON COLUMN analytics.view_percentual_escolas_infraestrutura.quantidade_escolas IS 'Total number of schools considered in the calculation.';
COMMENT ON COLUMN analytics.view_percentual_escolas_infraestrutura.percentual_escolas_com_internet IS 'Percentage of schools with internet access.';
COMMENT ON COLUMN analytics.view_percentual_escolas_infraestrutura.percentual_escolas_com_biblioteca IS 'Percentage of schools with a library.';
COMMENT ON COLUMN analytics.view_percentual_escolas_infraestrutura.percentual_escolas_com_laboratorio_informatica IS 'Percentage of schools with a computer laboratory.';
COMMENT ON COLUMN analytics.view_percentual_escolas_infraestrutura.percentual_escolas_com_laboratorio_ciencias IS 'Percentage of schools with a science laboratory.';
COMMENT ON COLUMN analytics.view_percentual_escolas_infraestrutura.percentual_escolas_com_agua_potavel IS 'Percentage of schools with drinking water.';
COMMENT ON COLUMN analytics.view_percentual_escolas_infraestrutura.percentual_escolas_com_energia_rede_publica IS 'Percentage of schools connected to the public electricity grid.';

-- ============================================================================
-- View: view_turmas_por_escola_uf
--
-- Purpose:
--     Returns class volume and average classes per school
--     by census year and state.
-- ============================================================================
DROP VIEW IF EXISTS analytics.view_turmas_por_escola_uf;
CREATE VIEW analytics.view_turmas_por_escola_uf AS
SELECT
    e.ano_censo,
    e.sigla_uf,
    SUM(t.quantidade_turmas::numeric) AS quantidade_turmas,
    COUNT(DISTINCT e.id_escola) AS quantidade_escolas,
    ROUND(SUM(t.quantidade_turmas::numeric) / NULLIF(COUNT(DISTINCT e.id_escola), 0), 2) AS media_turmas_por_escola
FROM analytics.dim_turma t
JOIN analytics.dim_escola e ON (t.id_escola = e.id_escola AND t.ano_censo = e.ano_censo)
GROUP BY e.ano_censo, e.sigla_uf;

COMMENT ON VIEW analytics.view_turmas_por_escola_uf IS 'Class volume and average classes per school grouped by census year and state.';
COMMENT ON COLUMN analytics.view_turmas_por_escola_uf.ano_censo IS 'School Census reference year.';
COMMENT ON COLUMN analytics.view_turmas_por_escola_uf.sigla_uf IS 'Brazilian state abbreviation.';
COMMENT ON COLUMN analytics.view_turmas_por_escola_uf.quantidade_turmas IS 'Total number of basic education classes.';
COMMENT ON COLUMN analytics.view_turmas_por_escola_uf.quantidade_escolas IS 'Total number of distinct schools.';
COMMENT ON COLUMN analytics.view_turmas_por_escola_uf.media_turmas_por_escola IS 'Average number of classes per school.';

-- ============================================================================
-- View: view_matriculas_por_uf_dependencia
--
-- Purpose:
--     Returns enrollment volume grouped by census year,
--     state and administrative dependency.
-- ============================================================================
DROP VIEW IF EXISTS analytics.view_matriculas_por_uf_dependencia;
CREATE VIEW analytics.view_matriculas_por_uf_dependencia AS
SELECT
    e.ano_censo,
    e.sigla_uf,
    d.dependencia_administrativa,
    SUM(m.quantidade_matriculas::numeric) AS quantidade_matriculas
FROM analytics.fato_matricula m
JOIN analytics.dim_escola e ON (m.id_escola = e.id_escola AND m.ano_censo = e.ano_censo)
LEFT JOIN analytics.dim_dependencia_administrativa d ON (e.id_dependencia_administrativa = d.id_dependencia_administrativa)
GROUP BY e.ano_censo, e.sigla_uf, d.dependencia_administrativa;

COMMENT ON VIEW analytics.view_matriculas_por_uf_dependencia IS 'Enrollment volume grouped by census year, state and administrative dependency.';
COMMENT ON COLUMN analytics.view_matriculas_por_uf_dependencia.ano_censo IS 'School Census reference year.';
COMMENT ON COLUMN analytics.view_matriculas_por_uf_dependencia.sigla_uf IS 'Brazilian state abbreviation.';
COMMENT ON COLUMN analytics.view_matriculas_por_uf_dependencia.dependencia_administrativa IS 'Administrative dependency classification (Federal, State, Municipal or Private).';
COMMENT ON COLUMN analytics.view_matriculas_por_uf_dependencia.quantidade_matriculas IS 'Total number of basic education enrollments.';

-- ============================================================================
-- View: view_razao_alunos_por_turma
--
-- Purpose:
--     Calculates the student-to-class ratio by census year
--     and state.
-- ============================================================================
DROP VIEW IF EXISTS analytics.view_razao_alunos_por_turma;
CREATE VIEW analytics.view_razao_alunos_por_turma AS
WITH matriculas_por_uf AS (
    SELECT
        e.ano_censo,
        e.sigla_uf,
        SUM(m.quantidade_matriculas::numeric) AS quantidade_matriculas
    FROM analytics.fato_matricula m
    JOIN analytics.dim_escola e ON (m.id_escola = e.id_escola AND m.ano_censo = e.ano_censo)
    GROUP BY e.ano_censo, e.sigla_uf
),
turmas_por_uf AS (
    SELECT
        e.ano_censo,
        e.sigla_uf,
        SUM(t.quantidade_turmas::numeric) AS quantidade_turmas
    FROM analytics.dim_turma t
    JOIN analytics.dim_escola e ON (t.id_escola = e.id_escola AND t.ano_censo = e.ano_censo)
    GROUP BY e.ano_censo, e.sigla_uf
)
SELECT
    m.ano_censo,
    m.sigla_uf,
    m.quantidade_matriculas,
    t.quantidade_turmas,
    ROUND(m.quantidade_matriculas / NULLIF(t.quantidade_turmas, 0), 2) AS razao_alunos_por_turma
FROM matriculas_por_uf m
JOIN turmas_por_uf t ON (m.ano_censo = t.ano_censo AND m.sigla_uf = t.sigla_uf);

COMMENT ON VIEW analytics.view_razao_alunos_por_turma IS 'Student-to-class ratio grouped by census year and state.';
COMMENT ON COLUMN analytics.view_razao_alunos_por_turma.ano_censo IS 'School Census reference year.';
COMMENT ON COLUMN analytics.view_razao_alunos_por_turma.sigla_uf IS 'Brazilian state abbreviation.';
COMMENT ON COLUMN analytics.view_razao_alunos_por_turma.quantidade_matriculas IS 'Total number of basic education enrollments.';
COMMENT ON COLUMN analytics.view_razao_alunos_por_turma.quantidade_turmas IS 'Total number of basic education classes.';
COMMENT ON COLUMN analytics.view_razao_alunos_por_turma.razao_alunos_por_turma IS 'Average number of students per class.'