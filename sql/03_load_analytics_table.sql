DELETE FROM "{target_schema}"."{target_table}"
WHERE "{target_year_column}" = :year;

INSERT INTO "{target_schema}"."{target_table}" (
    {insert_columns}
)
SELECT
    {select_columns}
FROM "{source_schema}"."{source_table}"
WHERE "{source_year_column}" = :year;