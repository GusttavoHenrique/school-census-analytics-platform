CREATE TABLE IF NOT EXISTS "{target_schema}"."{target_table}" (
    "{surrogate_key_column}" bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    {table_columns}
);