from pathlib import Path

import pandas as pd

from logger import logger


BASE_DIR = Path(__file__).resolve().parent.parent

FILE_PATH = BASE_DIR / "data" / "raw" / "Online_Retail.xlsx"

PROCESSED_DIR = BASE_DIR / "data" / "processed"

EXTRACTED_FILE = PROCESSED_DIR / "extracted_data.pkl"


def extract():

    logger.info("Début de l'extraction")

    logger.info("Lecture du fichier %s", FILE_PATH.name)

    df = pd.read_excel(FILE_PATH)

    logger.info(
        "Extraction terminée : %s lignes et %s colonnes",
        len(df),
        len(df.columns),
    )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_pickle(EXTRACTED_FILE)

    logger.info(
        "Données extraites enregistrées dans %s",
        EXTRACTED_FILE
    )

    return str(EXTRACTED_FILE)