from pathlib import Path

import pandas as pd

from logger import logger


def classify_transaction(row):
    invoice_no = str(row["InvoiceNo"])

    if invoice_no.startswith("C"):
        return "cancelled"

    if row["Quantity"] < 0:
        return "stock_adjustment"

    if row["UnitPrice"] <= 0:
        return "invalid_or_free"

    return "sale"


def transform(extracted_file_path):
    logger.info("Début de la transformation")

    # Lire le fichier produit par Extract
    df = pd.read_pickle(extracted_file_path)

    logger.info("Nombre de lignes initiales : %s", len(df))

    df = df.copy()

    # Classification métier
    df["transaction_type"] = df.apply(
        classify_transaction,
        axis=1
    )

    # Identification des doublons
    df["is_duplicate"] = df.duplicated(
        subset=[
            "InvoiceNo",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "UnitPrice",
            "CustomerID",
            "Country"
        ],
        keep="first"
    )

    # Raison principale d’exclusion
    df["exclusion_reason"] = pd.Series(
        pd.NA,
        index=df.index,
        dtype="string"
    )

    conditions = [
        df["transaction_type"] != "sale",
        df["CustomerID"].isna(),
        df["Description"].isna(),
        df["is_duplicate"]
    ]

    reasons = [
        "not_a_sale",
        "missing_customer",
        "missing_description",
        "duplicate"
    ]

    for condition, reason in zip(conditions, reasons):
        df.loc[
            condition & df["exclusion_reason"].isna(),
            "exclusion_reason"
        ] = reason

    df["exclusion_reason"] = df["exclusion_reason"].fillna(
        "clean_sale"
    )

    clean_sales_df = df[
        df["exclusion_reason"] == "clean_sale"
    ].copy()

    rejected_df = df[
        df["exclusion_reason"] != "clean_sale"
    ].copy()

    clean_sales_df["CustomerID"] = (
        clean_sales_df["CustomerID"]
        .astype("Int64")
        .astype("string")
    )

    clean_sales_df["total_amount"] = (
        clean_sales_df["Quantity"]
        * clean_sales_df["UnitPrice"]
    )

    # Contrôles qualité
    assert len(clean_sales_df) + len(rejected_df) == len(df)
    assert clean_sales_df["CustomerID"].isna().sum() == 0
    assert clean_sales_df["Description"].isna().sum() == 0
    assert (clean_sales_df["Quantity"] <= 0).sum() == 0
    assert (clean_sales_df["UnitPrice"] <= 0).sum() == 0
    assert clean_sales_df["is_duplicate"].sum() == 0

    logger.info("Tous les contrôles qualité sont validés.")

    logger.info("Ventes propres : %s", len(clean_sales_df))
    logger.info("Lignes rejetées : %s", len(rejected_df))

    logger.info(
        "Répartition des exclusions :\n%s",
        df["exclusion_reason"].value_counts()
    )

    # Sauvegarde dans data/processed
    processed_dir = Path(extracted_file_path).parent

    clean_file = processed_dir / "clean_sales.pkl"
    rejected_file = processed_dir / "rejected_sales.pkl"

    clean_sales_df.to_pickle(clean_file)
    rejected_df.to_pickle(rejected_file)

    logger.info("Fichier clean : %s", clean_file)
    logger.info("Fichier rejected : %s", rejected_file)

    logger.info("Fin de la transformation")

    return {
        "clean_file": str(clean_file),
        "rejected_file": str(rejected_file)
    }