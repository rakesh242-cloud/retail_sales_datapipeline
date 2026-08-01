from extract import extract
from transform import transform
from load import load
from logger import logger


def main():
    logger.info("Démarrage du pipeline Retail Sales")

    raw_df = extract()

    clean_sales_df, rejected_df = transform(raw_df)

    load(clean_sales_df, rejected_df)

    logger.info("Pipeline terminé avec succès")


if __name__ == "__main__":
    main()