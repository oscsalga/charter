import pandas as pd
from glob import glob
import os


output_excel = r'all_excels.xlsx'


def auto_width_columns(df, worksheet, formato):
    for s, col in enumerate(df.columns):
        column_len = max(df[col].astype(str).str.len().max(), len(col))
        worksheet.set_column(s, s, column_len - 10, formato)
#List all excel files in folder



with pd.ExcelWriter(output_excel) as writer:


    for file in glob('*.xlsx'):
        if output_excel in file:
            continue
        sheet_name = str(pd.ExcelFile(file).sheet_names[0]).replace("xlsx", "")

        df = pd.read_excel(file)
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        workbook = writer.book
        worksheet = writer.sheets[str(sheet_name)]
        formato = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
        titulo = workbook.add_format({'bg_color': '19b2e7'})
        worksheet.conditional_format(0, 0, 0, worksheet.dim_colmax,
                                     {'criteria': ">", 'value': -1, 'type': 'cell', 'format': titulo})
        auto_width_columns(df, worksheet, formato)
