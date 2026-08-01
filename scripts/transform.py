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


def transform(df):
    logger.info("Début de la transformation")
    logger.info("Nombre de lignes initiales : %s", len(df))

    df = df.copy()

    # Classification métier
    df["transaction_type"] = df.apply(
        classify_transaction,
        axis=1
    )

    # Identification des doublons avant toute modification
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

    # Séparation des données
    clean_sales_df = df[
        df["exclusion_reason"] == "clean_sale"
    ].copy()

    rejected_df = df[
        df["exclusion_reason"] != "clean_sale"
    ].copy()

    # Conversion de CustomerID en identifiant texte
    clean_sales_df["CustomerID"] = (
        clean_sales_df["CustomerID"]
        .astype("Int64")
        .astype("string")
    )

    # Création d’une mesure de chiffre d’affaires
    clean_sales_df["total_amount"] = (
        clean_sales_df["Quantity"]
        * clean_sales_df["UnitPrice"]
    )

    logger.info(
        "Ventes propres : %s",
        len(clean_sales_df)
    )

    logger.info(
        "Lignes rejetées : %s",
        len(rejected_df)
    )

    logger.info(
        "Répartition des exclusions :\n%s",
        df["exclusion_reason"].value_counts()
    )

    logger.info("Fin de la transformation")


    logger.info("Ventes propres : %s", len(clean_sales_df))
    logger.info("Lignes rejetées : %s", len(rejected_df))

    # ==========================
    # Contrôles qualité
    # ==========================

    assert len(clean_sales_df) + len(rejected_df) == len(df)

    assert clean_sales_df["CustomerID"].isna().sum() == 0

    assert clean_sales_df["Description"].isna().sum() == 0

    assert (clean_sales_df["Quantity"] <= 0).sum() == 0

    assert (clean_sales_df["UnitPrice"] <= 0).sum() == 0

    assert clean_sales_df["is_duplicate"].sum() == 0

    logger.info("Tous les contrôles qualité sont validés.")

    logger.info("Fin de la transformation")

    return clean_sales_df, rejected_df

