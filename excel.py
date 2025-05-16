import datetime
import openpyxl

from schemas import *
from log import Log


class ExcelBook:
    def __init__(self, file_name_prefix: str = ""):
        self.file_name = (
            file_name_prefix + datetime.datetime.now().strftime("%Y-%m-%d") + ".xlsx"
        )

    def write(self, bond_list: list[Bond], log: Log) -> None:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(Bond.headers())
        for bond in bond_list:
            ws.append(bond.as_list)
        # Center data
        self.center_worksheet(ws)
        # Auto-width
        self.auto_width(ws)
        wb.save(self.file_name)
        log.info(f"Результаты сохранены в файл {self.file_name}.")

    def center_worksheet(
        self, worksheet: openpyxl.worksheet.worksheet.Worksheet
    ) -> None:
        """
        Centering data in worksheet.
        """
        center_alignment = openpyxl.styles.Alignment(horizontal="center")
        for row in worksheet.iter_rows(
            min_row=1,
            max_row=worksheet.max_row,
            min_col=1,
            max_col=worksheet.max_column,
        ):
            for cell in row:
                cell.alignment = center_alignment
        return

    def auto_width(self, worksheet: openpyxl.worksheet.worksheet.Worksheet) -> None:
        """
        Sets width to fit content
        """
        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) for cell in column_cells if cell.value)
            worksheet.column_dimensions[
                openpyxl.utils.get_column_letter(column_cells[0].col_idx)
            ].width = (length * 1.2)
        return