CREATE TABLE IF NOT EXISTS "{target_schema}"."dim_dependencia_administrativa" (
    "sk_dependencia_administrativa" bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "id_dependencia_administrativa" text UNIQUE NOT NULL,
    "dependencia_administrativa" text NOT NULL
);

INSERT INTO "{target_schema}"."dim_dependencia_administrativa" (
    "id_dependencia_administrativa",
    "dependencia_administrativa"
)
VALUES
    ('1', 'federal'),
    ('2', 'estadual'),
    ('3', 'municipal'),
    ('4', 'privada')
ON CONFLICT ("id_dependencia_administrativa") DO UPDATE
SET "dependencia_administrativa" = EXCLUDED."dependencia_administrativa";

CREATE TABLE IF NOT EXISTS "{target_schema}"."dim_localizacao" (
    "sk_localizacao" bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "id_localizacao" text UNIQUE NOT NULL,
    "localizacao" text NOT NULL
);

INSERT INTO "{target_schema}"."dim_localizacao" (
    "id_localizacao",
    "localizacao"
)
VALUES
    ('1', 'urbana'),
    ('2', 'rural')
ON CONFLICT ("id_localizacao") DO UPDATE
SET "localizacao" = EXCLUDED."localizacao";