CREATE TABLE apps_log.crossroads_automation_log
(
    id                SERIAL PRIMARY KEY NOT NULL,
    log_datetime      TIMESTAMP          NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'US/Pacific'),
    file_location     TEXT,
    created_file_name TEXT,
    entry_count       INT,
    failure_step      TEXT,
    is_uploaded       BOOLEAN            NOT NULL DEFAULT (FALSE)
);
