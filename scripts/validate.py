from database import get_connection
from logger import logger


def validate_load(expected_clean, expected_rejected):
    connection = None

    try:
        logger.info("Début de la validation PostgreSQL")

        connection = get_connection()

        with connection.cursor() as cursor:

            # Nombre réel de ventes propres
            cursor.execute("SELECT COUNT(*) FROM clean_sales;")
            actual_clean = cursor.fetchone()[0]

            # Nombre réel de lignes rejetées
            cursor.execute("SELECT COUNT(*) FROM rejected_sales;")
            actual_rejected = cursor.fetchone()[0]

        logger.info(
            "clean_sales : attendu=%s | PostgreSQL=%s",
            expected_clean,
            actual_clean
        )

        logger.info(
            "rejected_sales : attendu=%s | PostgreSQL=%s",
            expected_rejected,
            actual_rejected
        )

        # Validation
        if actual_clean != expected_clean:
            raise ValueError(
                f"Validation échouée pour clean_sales : "
                f"attendu={expected_clean}, trouvé={actual_clean}"
            )

        if actual_rejected != expected_rejected:
            raise ValueError(
                f"Validation échouée pour rejected_sales : "
                f"attendu={expected_rejected}, trouvé={actual_rejected}"
            )

        logger.info("Validation PostgreSQL réussie ✅")

    except Exception:
        logger.exception("Échec de la validation PostgreSQL")
        raise

    finally:
        if connection is not None:
            connection.close()
            logger.info("Connexion PostgreSQL fermée")