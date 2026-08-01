import pandas as pd
from logger import logger

def extract():
    df = pd.read_excel("C:\\Users\\jouba\\Desktop\\CodEnfant\\python\\retail_sales_pipeline\\data\\raw\\Online_Retail.xlsx")
    logger.info("Lecture du fichier Online retail.xlsx")
    return df