import pandas as pd
from sqlalchemy.orm import Session
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from pathlib import Path
from icecream import ic


def generate_excel(file_path:str,datas:list,sheet_name:str,handwritten:bool=False):
    wb = Workbook(write_only=True)
    ws = wb.create_sheet(sheet_name)

    df = pd.DataFrame(datas)

    for r in dataframe_to_rows(df, index=False, header=not handwritten):
        ws.append(r)

    ic("Excel file creted successfully")
    wb.save(file_path)