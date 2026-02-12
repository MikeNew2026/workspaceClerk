from pathlib import Path
from dataclasses import dataclass


@dataclass
class ImportResult:
    raw_string: str
    level: int = 0
    module: str | None = None
    name: str | None = None


def is_relative_import_package(package_path_in: Path, file_import_in: Path,
                               imprt: ImportResult) -> bool:
    """Блок проверок"""

    # для простых прямых импортов без путей, например: "import app1"
    # то есть когда import не путь а прямое указание импортируемого модуля
    if not imprt.module and not '.' in imprt.name and imprt.level == 0:
        return package_path_in.parts[-1] == imprt.name

    imp_mod = imprt.module.split('.') if imprt.module else []
    imp_name = imprt.name.split('.') if imprt.name else []
    import_combo = Path(*imp_mod, *imp_name)  # соединить модуль(from) и наименование(import)

    if not imprt.module and '.' in imprt.name and imprt.level == 0:
        # сравнение сегментов путей "пути пакета" и "пути импорта"
        if package_path_in.parts[-len(Path(*imp_name).parts):] == Path(*imp_name).parts:
            return True

    # для случаев когда импорты выглядят так: from src.app import main (задача отсечь main)
    if imprt.module and imprt.level == 0:
        # print(44)
        while len(import_combo.parts) > 0:
            if package_path_in.parts[-len(import_combo.parts):] == import_combo.parts:
                return True
            import_combo = import_combo.parent

    # для импорта типа "import src.app1" <-> нужно сделать выход из файла
    # if not imprt.module and imprt.level == 0:
    #     file_import_in = file_import_in.parent

    # все остальные случаи импорты типа:  "from . import app1"
    for _ in range(imprt.level):  # спуститься с импортированного файла на заданный уровень (level раз)
        file_import_in = file_import_in.parent

    gen_file = file_import_in / import_combo  # путь к импортируемому файлом модулю установлен

    # print(f"{file_import_in} -> file_import_in")
    # print(f"{package_path_in} -> package_path_in")
    # print(f"{gen_file} -> gen_file")

    if gen_file == package_path_in:  # сравнить пути пакета и пути импорта из файла.
        return True

    else:  # они могут быть не равны если например в импорте есть объекты из самого файла пакета, например import app1.x
        while gen_file != file_import_in:
            if gen_file == package_path_in:
                return True
            gen_file = gen_file.parent  # отсечка не файловых объектов импорта

    return False


def test_is_relative_import_package():
    # Тест нужно проводить в комплексе с реальным названием файлов. Здесь всё расставлено в ручную
    @dataclass
    class RelativeTest:
        imprt: ImportResult
        file_imports: Path
        package_path: Path
        result: bool

    test_data = [
        # import src.app1
        # ImportResult(raw_string='import src.app1', level=0, module=None, name='src.app1')

        RelativeTest(
            imprt=ImportResult(raw_string='import src.app1', level=0, module=None, name='src.app1'),
            file_imports=Path(r'home/test/main.py'),
            package_path=Path(r'home/test/src/app1'),
            result=True,
        ),

        RelativeTest(
            imprt=ImportResult(raw_string='from .. import app1', level=2, module='src', name='app1'),
            file_imports=Path(r'home/test/main.py'),
            package_path=Path(r'home/test/src/app1'),
            result=False,
        ),

        RelativeTest(
            imprt=ImportResult(raw_string='import app1', level=0, module=None, name='app1'),
            file_imports=Path(r'home/test/demo/help.py'),
            package_path=Path(r'home/test/src/app1'),
            result=True,
        ),

        RelativeTest(
            imprt=ImportResult(raw_string='import src.app1', level=0, module='src', name='app1'),
            file_imports=Path(r'home/test/demo/help.py'),
            package_path=Path(r'home/test/src/app1'),
            result=True,
        ),

        RelativeTest(
            imprt=ImportResult(raw_string='from src import app1', level=0, module='src', name='app1'),
            file_imports=Path(r'home/test/demo/help.py'),
            package_path=Path(r'home/test/src/app1'),
            result=True,
        ),

        RelativeTest(
            imprt=ImportResult(raw_string='from src import app1', level=0, module='src.app1', name='main'),
            file_imports=Path(r'home/test/demo/help.py'),
            package_path=Path(r'home/test/src/app1'),
            result=True,
        ),

        RelativeTest(
            imprt=ImportResult(raw_string='from fastapi.app1 import main', level=0, module='fastapi.app1', name='main'),
            file_imports=Path(r'home/test/demo/help.py'),
            package_path=Path(r'home/test/src/app1'),
            result=False,
        ),

        RelativeTest(
            imprt=ImportResult(raw_string='from .src import app1', level=1, module='src', name='app1'),
            file_imports=Path(r'home/test/main.py'),  # внимание на уровни вложенности
            package_path=Path(r'home/test/src/app1'),
            result=True,
        ),

        RelativeTest(
            imprt=ImportResult(raw_string='from ..src import app1', level=2, module='src', name='app1'),
            file_imports=Path(r'home/test/demo/help.py'),
            package_path=Path(r'home/test/src/app1'),
            result=True,
        ),

    ]

    for exmp in test_data:
        res = is_relative_import_package(
            package_path_in=exmp.package_path,
            file_import_in=exmp.file_imports,
            imprt=exmp.imprt
        )
        assert res == exmp.result, f"Ошбика результата для import {exmp.imprt.name} and from {exmp.imprt.module}"
        # print(f"{exmp.imprt.name} -> {res}")


if __name__ == '__main__':
    test_is_relative_import_package()
