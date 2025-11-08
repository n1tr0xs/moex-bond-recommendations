import datetime
import logging
import openpyxl

from schemas import *

logger = logging.getLogger("Excel")


class ExcelBook:
    def __init__(self, file_name: str = None):
        self.file_name = file_name or datetime.datetime.now().strftime("%d.%m.%Y")

    def write_bonds(self, bond_list: list[Bond]) -> None:
        """
        Writes given bond_list to excel file.
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        logger.info("Запись данных в файл...")
        # Add data to file
        ws.append(Bond.headers())
        for bond in bond_list:
            ws.append(bond.as_list)
        # Center data
        logger.info("Центрирование ячеек таблицы...")
        self._center_worksheet(ws)
        # Auto-width
        logger.info("Подбор ширины ячеек таблицы")
        self.auto_width(ws)
        # Saving file
        fileno = 0
        while True:
            try:
                logger.info(f"Сохранение в файл {self.file_name}.")
                wb.save(self.file_name + (f"({fileno})" if fileno else "") + ".xlsx")
            except PermissionError:
                logger.warning(f"Не удалось сохранить файл. Изменение имени файла...")
                fileno += 1
            else:
                logger.info("Файл сохранен.")
                return

    def _center_worksheet(
        self, worksheet: openpyxl.worksheet.worksheet.Worksheet
    ) -> None:
        """
        Centers data in worksheet.
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

    def get_file_name(self) -> str:
        return self.file_name
