from io import StringIO
from database import get_connection
from logger import logger


def copy_dataframe(
    connection,
    dataframe,
    table_name,
    columns
):
    buffer = StringIO()

    dataframe[columns].to_csv(
        buffer,
        index=False,
        header=False,
        na_rep="",
        sep="\t"
    )

    buffer.seek(0)

    columns_sql = ", ".join(columns)

    copy_sql = f"""
        COPY {table_name} ({columns_sql})
        FROM STDIN
        WITH (
            FORMAT CSV,
            DELIMITER E'\\t',
            NULL '',
            QUOTE '"'
        )
    """

    with connection.cursor() as cursor:
        with cursor.copy(copy_sql) as copy:
            while data := buffer.read(1024 * 1024):
                copy.write(data)


def load(clean_sales_df, rejected_df):
    connection = None

    clean_columns = [
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country",
        "transaction_type",
        "total_amount"
    ]

    rejected_columns = [
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country",
        "transaction_type",
        "exclusion_reason",
        "is_duplicate"
    ]

    clean_column_mapping = {
        "InvoiceNo": "invoice_no",
        "StockCode": "stock_code",
        "Description": "description",
        "Quantity": "quantity",
        "InvoiceDate": "invoice_date",
        "UnitPrice": "unit_price",
        "CustomerID": "customer_id",
        "Country": "country"
    }

    rejected_column_mapping = clean_column_mapping.copy()

    try:
        logger.info("Début du chargement PostgreSQL")

        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
            TRUNCATE TABLE clean_sales, rejected_sales
            RESTART IDENTITY;
            """)

        logger.info("Tables vidées avant le rechargement")

        clean_to_load = clean_sales_df.rename(
            columns=clean_column_mapping
        ).copy()

        rejected_to_load = rejected_df.rename(
            columns=rejected_column_mapping
        ).copy()

        clean_db_columns = [
            "invoice_no",
            "stock_code",
            "description",
            "quantity",
            "invoice_date",
            "unit_price",
            "customer_id",
            "country",
            "transaction_type",
            "total_amount"
        ]

        rejected_db_columns = [
            "invoice_no",
            "stock_code",
            "description",
            "quantity",
            "invoice_date",
            "unit_price",
            "customer_id",
            "country",
            "transaction_type",
            "exclusion_reason",
            "is_duplicate"
        ]

        copy_dataframe(
            connection,
            clean_to_load,
            "clean_sales",
            clean_db_columns
        )

        logger.info(
            "%s ventes propres chargées",
            len(clean_to_load)
        )

        copy_dataframe(
            connection,
            rejected_to_load,
            "rejected_sales",
            rejected_db_columns
        )

        logger.info(
            "%s lignes rejetées chargées",
            len(rejected_to_load)
        )

        connection.commit()

        logger.info("Chargement PostgreSQL terminé avec succès")

    except Exception:
        if connection is not None:
            connection.rollback()

        logger.exception(
            "Erreur pendant le chargement PostgreSQL"
        )

        raise

    finally:
        if connection is not None:
            connection.close()
            logger.info("Connexion PostgreSQL fermée")