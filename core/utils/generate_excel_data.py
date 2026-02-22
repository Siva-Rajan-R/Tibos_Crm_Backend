import pandas as pd
from sqlalchemy.orm import Session
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from pathlib import Path
from icecream import ic


def init_excel(sheet_name: str):
    wb = Workbook(write_only=True)
    ws = wb.create_sheet(sheet_name)
    return wb, ws


def append_excel_rows(ws, datas: list, write_header: bool):
    if not datas:
        return

    df = pd.DataFrame(datas)

    for row in dataframe_to_rows(
        df,
        index=False,
        header=write_header
    ):
        ws.append(row)
