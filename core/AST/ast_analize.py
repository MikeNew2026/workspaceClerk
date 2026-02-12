from core.AST.is_relative_import_packages import is_relative_import_package
from core.AST.import_finder import ast_parser_imports, ImportResult
from core.utils.directory_walker_filtered import directory_walker_filtered
from pathlib import Path
import tokenize


class AstImportsManager:
    def __init__(self, root_path_in):
        self._root_path = root_path_in
        self.imports = {}
        self._start()

    def _start(self):
        python_files_generator = directory_walker_filtered(
            root_path_in=self._root_path,
            extensions_filter={'.py', },
            dirs_filter={'.venv', 'venv', 'idea', '.idea'},
            dirs_filter_exclude=True,
        )

        # 1 раз сканируются все файлы при инициализации, заполняя список imports
        for file in python_files_generator:
            source = self.read_file(file)
            imprts: list[ImportResult] = ast_parser_imports(source_code_in=source)
            if imprts:
                self.imports[file] = imprts

    @staticmethod
    def read_file(file_path) -> str | None:
        if not file_path.exists():
            raise FileNotFoundError(f'Файл `{file_path}` не существует')

        try:
            with open(file=file_path, mode='rb') as f:
                encoding = tokenize.detect_encoding(f.readline)[0]
        except Exception as err:
            raise FileNotFoundError(f'Файл `{file_path}` ошибка при чтении кодировки: {err}')

        try:
            with open(file=file_path, encoding=encoding) as f:
                content = f.read()
                return content
        except Exception as err:
            raise FileNotFoundError(f'Файл `{file_path}` ошибка при чтении кодировки: {err}')

    def get_package_relative_files(self, package_path: Path) -> list[Path]:
        relative_files = []
        for file, imprts in self.imports.items():
            for imp in imprts:
                is_package = is_relative_import_package(
                    imprt=imp,
                    file_import_in=file,
                    package_path_in=package_path,
                )
                if is_package:
                    relative_files.append(file)
        return relative_files


from pathlib import Path

if __name__ == '__main__':
    root_path = Path(r'C:\Users\MikeCoder\Desktop\DEMO')
    conv = AstImportsManager(root_path_in=root_path)
    conv.get_package_relative_files(package_path=Path(r'C:\Users\MikeCoder\Desktop\DEMO\src\app1'))
