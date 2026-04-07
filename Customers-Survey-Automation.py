import sys
from datetime import datetime as dt
from datetime import timedelta
import pandas as pd
from pykeepass import PyKeePass
import config
from analytics_platform_connection import AnalyticsPlatformConnection
from sftp_connection import SftpConnection
from prefect import flow
from prefect_email import EmailServerCredentials, email_send_message

######################################################################################################################

@flow
def prefect_email(error_message):
    email_server_credentials = EmailServerCredentials.load("prefect-ddbot-email")
    email_addresses = [email_to_notify]
    print(error_message)
    for email_address in email_addresses:
        email_send_message.with_options(name=f"email {email_address}").submit(
            email_server_credentials=email_server_credentials,
            subject="Customer Daily Survey - Script Error",
            msg=error_message,
            email_to=email_address,
        )


# accesses kdbx database to pull credentials and potentially ssl files
try:
    # initializes dictionary for logging
    log_dictionary = {
        'file_location': None,
        'created_file_name': None,
        'entry_count': None,
        'failure_step': None,
        'is_uploaded': False
    }
    # connect to KeePass database
    db = PyKeePass(filename=config.KDBX_FILE, keyfile=config.KEY_PATH)
    # Connect to SQL production database
    sql_production = AnalyticsPlatformConnection(keepass_db=db, keepass_entry=credential_entry)
    sql_production.create_connection(use_ssl=True)
    db_engine_production = sql_production.can_connect()
    print('STATUS: Connected to Database')
except:
    error = 'Failed connection to database'
    print(error)
    sql_production.kill_connection()
    prefect_email(error)
    sys.exit()

# Chooses the date ramge to query data from
TODAY = dt.today().date()
START_OF_WEEK = TODAY - timedelta(days=7)
END_OF_WEEK = TODAY - timedelta(days=1)


customers_query = f"""
SELECT
    customer_id,
    first_name,
    last_name,
    email,
    phone_number,
    date_of_birth,
    gender,
    city,
    state,
    country,
    postal_code
FROM
    customers
WHERE
    active = TRUE and record_date BETWEEN '{START_OF_WEEK}' AND '{END_OF_WEEK}'
ORDER BY
    last_name,
    first_name;
        """

missing_data_query = """
WITH valid_date_range AS (
    -- Find all valid dates within the last 7 days:
    -- - Weekdays only (Monday through Friday)
    -- - At least 2 days behind current date
    SELECT
        date
    FROM (
        SELECT
            (CURRENT_DATE - INTERVAL '1 day' * count)::DATE AS date
        FROM GENERATE_SERIES(1, 7) AS days_past(count)
    ) AS last_week
    WHERE EXTRACT(DOW FROM date) BETWEEN 1 AND 5  -- Monday=1 to Friday=5
      AND date <= CURRENT_DATE - INTERVAL '2 days'
)
SELECT
    -- Trigger flag if the most recent valid date has no records
    MAX(customer_data.record_date::DATE) < MAX(valid_date_range.date) AS missing_data_flag,
    -- Display the most recent recorded date
    'Last recorded data on ' || TO_CHAR(MAX(customer_data.record_date), 'FMMM/FMDD/YY') AS last_record_detail
FROM customer_data
CROSS JOIN valid_date_range
WHERE customer_data.status = 'completed';
        """

# queries SQL database for missing data and Customer data
try:
    missing_data_result = pd.read_sql(sql=missing_data_query, con=db_engine_production)
    is_missing_data = missing_data_result['trigger'][0]
    # True = missing data, False = has data
    customers_results = pd.read_sql(sql=customers_query, con=db_engine_production)
    entry_count = customers_results.shape[0]
    print('STATUS: Successfully queried data')
except:
    error = 'Failure with query'
    print(error)
    log_dictionary['failure_step'] = str(error)
    log = pd.DataFrame([log_dictionary])
    log.to_sql(con=db_engine_production, schema='apps_log', name='customers_automation_log', if_exists='append',
               index=False)
    sql_production.kill_connection()
    prefect_email(error)
    sys.exit()

# if there are missing data, do not create and upload data
if is_missing_data:
    error = 'Missing data'
    print(error)
    log_dictionary['failure_step'] = error
    log = pd.DataFrame([log_dictionary])
    log.to_sql(con=db_engine_production, schema='apps_log', name='customers_automation_log',
               if_exists='append', index=False)
    sql_production.kill_connection()
    prefect_email(error)
    sys.exit()

print('STATUS: No missing data')

# if there is no data and no missing visit alert, log and quit out
if entry_count == 0:
    log_dictionary['failure_step'] = 'No Data'
    print('NO DATA')
    log = pd.DataFrame([log_dictionary])
    log.to_sql(con=db_engine_production, schema='apps_log', name='customers_automation_log',
               if_exists='append', index=False)
    sql_production.kill_connection()
    sys.exit()

# create Excel file with Customer data
try:
    customers_file_name = f"{START_OF_WEEK.strftime('%m%d%Y')}-{END_OF_WEEK.strftime('%m%d%Y')} claims by site {TODAY.strftime('%m%d%Y')}.xlsx"
    customers_file_path = config.FILE_OUTPUT_DIRECTORY.joinpath(customers_file_name)
    customers_results.to_excel(customers_file_path, index=False)
    log_dictionary['created_file_name'] = customers_file_name
    log_dictionary['file_location'] = str(config.FILE_OUTPUT_DIRECTORY)
    log_dictionary['entry_count'] = entry_count
    print('STATUS: Finished creating file')
except:
    error = 'Failed exporting Excel file'
    print(error)
    log_dictionary['failure_step'] = str(error)
    log = pd.DataFrame([log_dictionary])
    log.to_sql(con=db_engine_production, schema='apps_log', name='customers_automation_log', if_exists='append',
               index=False)
    sql_production.kill_connection()
    prefect_email(error)
    sys.exit()

# upload excel file to Customer via SFTP
try:
    send_result = SftpConnection(keepass_db=db, keepass_entry='customers', exported_file=customers_file_path,
                                 log=log_dictionary)
    if send_result != 'SUCCESS':
        raise Exception
    log_dictionary['is_uploaded'] = True
    print('SUCCESS: Finished uploading')
except:
    error = 'Could not upload file via SFTP'
    print(error)
    log_dictionary['failure_step'] = str(error)
    prefect_email(error)
# log automation status and kill the SQL connection
finally:
    log = pd.DataFrame([log_dictionary])
    log.to_sql(con=db_engine_production, schema='apps_log', name='customers_automation_log', if_exists='append',
               index=False)
    sql_production.kill_connection()
    sys.exit()
