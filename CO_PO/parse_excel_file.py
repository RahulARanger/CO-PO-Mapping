import gc
import logging
import pathlib
import typing
import matlab.engine
import matlab
from openpyxl import load_workbook
from openpyxl.workbook import Workbook
from openpyxl.worksheet.table import Table
from openpyxl.utils.cell import coordinate_to_tuple
import io


def starting_table_number(table: Table):
    return coordinate_to_tuple(table.ref.split(":")[0])


def parse_tables(tables_to_consider: int, workbook: Workbook, *sheets: typing.List[str]):
    """
    Parse the tables in the workbook.

    :param tables_to_consider: The Top n tables to consider.
    :param workbook: The workbook to parse.
    :param sheets: The sheets to parse.
    :return: The parsed tables.
    """

    for SHEET in sheets:
        _sheet = workbook[SHEET]
        _tables = sorted(_sheet.tables.values(), key=lambda _: starting_table_number(_))

        if len(_tables) < tables_to_consider:
            raise ValueError(
                f"Sheet: {SHEET} has less than {tables_to_consider} tables, Remember"
                f"first {tables_to_consider} tables are considered\nPlease refer Excel Input Format in 'How To' Tab "
            )

        for table in _tables[:tables_to_consider]:
            table: Table = table
            yield [
                [CELL.value for CELL in row]
                for index, row in enumerate(_sheet[table.ref]) if index != 0
            ]


class Engine:
    def __init__(self):
        super().__init__()
        self.matlab_engine = matlab.engine.start_matlab()
        self.matlab_engine.cd(str(pathlib.Path(__file__).parent / "Scripts"))
        self.raw = []

    def stop_engine(self):
        self.matlab_engine.quit() if self.matlab_engine else ...
        del self.matlab_engine
        gc.collect()

    def actual_parse(self, saved_excel: pathlib.Path, exams: int):
        workbook = load_workbook(saved_excel, read_only=False)
        logging.info("Workbook loaded")

        output = io.StringIO()
        error = io.StringIO()

        if len(workbook.sheetnames) < (exams + 1):
            raise ValueError(
                "There are not enough sheets in the workbook\nWe need X + 1 sheets, where X = Number of Exams\nRefer "
                "Sample Input from the 'How To' Tab "
            )

        sheets = workbook.sheetnames[-(exams + 1):]
        # cot, co_po, weightage, expected = (matlab.double(_) for _ in parse_tables(4, workbook, sheets[0]))
        gc.collect()

        self.matlab_engine.bridge(
            *(matlab.double(_) for _ in parse_tables(4, workbook, sheets[0])),
            *(matlab.double(_) for _ in parse_tables(2, workbook, *sheets[1:])),
            stdout=output,
            stderr=error,
            nargout=0
        )

        workbook.close()

        output.seek(0)
        error.seek(0)

        if saved_excel.exists():
            saved_excel.unlink()
            parent = saved_excel.parent
            if parent.exists() and not list(parent.iterdir()):
                parent.rmdir()

        return output.read(), error.read()


