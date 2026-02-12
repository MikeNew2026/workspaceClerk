import re
import ast
from dataclasses import dataclass

_IMPORT_FINDER_PATTERNS_IMPORT = (
    # простые импорты : import app, import src.app
    # в шаблоне должны быть прописаны группы name
    # шаблоны можно расширять в случае необходимости (важно следить за порядком от частного к общему)
    r"^(\s+?)?(?!#)?import\s+?(?P<name>[\w\.]+)",
)

_IMPORT_FINDER_PATTERNS_IMPORT_FROM = (
    # модульные импорты : "from . import app", "from src.app import *", "from ..app import main" и т.д.
    # в шаблоне должны быть прописаны группы level, module, name
    # шаблоны можно расширять в случае необходимости (важно следить за порядком от частного к общему)
    r"from\s+?(?P<level>!?\.+)?(?P<module>!?[\w\.]+?)?\s+?import\s+?(?P<name>[\w\*]+)",
)

_IMPORT_FINDER_PATTERNS_POST = (
    # Шаблон для парсинга пост импортов вида from src import [app1, app2, app3]
    r",\s+?(\w+)",
)


@dataclass
class ImportResult:
    raw_string: str
    level: int = 0
    module: str | None = None
    name: str | None = None


class _ImportFinder(ast.NodeVisitor):
    """
    Поиск импортов в коде python.
    ast выдает сырые строки, которые потом анализируются регулярными выражениями, разбирая строку на
    import и module. Для относительных импортов типа "from ... import main" вычисляется уровень вложенности
    На выходе возвращается объект.
    (Выбран гибридный подход, так как AST нормализует импорты вида "from ... import main" убирая уровни вложенности)
    """

    def __init__(self, source):
        self.source = source
        self.imports = []

    def visit_Import(self, node):
        line = self.source.split('\n')[node.lineno - 1]
        imp = self.regex_parse_import_names(import_node=line.strip())
        self.imports.append(imp)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        line = self.source.split('\n')[node.lineno - 1]
        imp = self.regex_parse_import_from(import_node=line.strip())
        self.imports.append(imp)

        for pattern in _IMPORT_FINDER_PATTERNS_POST:
            post_import = re.findall(pattern, line)
            if post_import:
                for i in post_import:
                    self.imports.append(
                        ImportResult(
                            raw_string=line,
                            level=imp.level,
                            module=imp.module,
                            name=i,
                        )
                    )

        self.generic_visit(node)

    @staticmethod
    def regex_parse_import_from(import_node: str):
        for ptrn in _IMPORT_FINDER_PATTERNS_IMPORT_FROM:
            match = re.match(ptrn, import_node)
            if hasattr(match, 'groupdict'):
                level = None
                module = None
                name = None

                keys = match.groupdict()
                if 'level' in keys and 'module' in keys and 'name' in keys:
                    level = match.group('level')
                    module = match.group('module')
                    name = match.group('name')

                if 'module' in keys and 'name' in keys:
                    module = match.group('module')
                    name = match.group('name')

                return ImportResult(
                    level=level.count('.') if level else 0,
                    module=module,
                    name=name,
                    raw_string=import_node,
                )

        raise Exception(f'Импорт `{import_node}` не был обработан.')

    @staticmethod
    def regex_parse_import_names(import_node: str):
        """Поиск импортов в названиях"""
        for ptrn in _IMPORT_FINDER_PATTERNS_IMPORT:
            match = re.match(ptrn, import_node)
            if hasattr(match, 'groupdict') and 'name' in match.groupdict():
                return ImportResult(
                    level=0,
                    module=None,
                    name=match.group('name'),
                    raw_string=import_node,
                )

        raise Exception(f'Импорт `{import_node}` не был обработан.')


def ast_parser_imports(source_code_in: str) -> list[ImportResult]:
    tree = ast.parse(source_code_in)
    finder = _ImportFinder(source_code_in)
    finder.visit(tree)
    return finder.imports


def test_ast_parser_imports():
    from dataclasses import dataclass
    @dataclass
    class FinderTest:
        code: str
        level: int = 0
        module: str | None = None
        name: str | None = None

    tests_set = [
        # ## простые тесты получен ли результат(resultat) и кода(code)
        FinderTest(code="import app1", level=0, module=None, name='app1'),
        FinderTest(code="import src.app1", level=0, module=None, name='src.app1'),
        FinderTest(code="from src import app1", level=0, module='src', name='app1'),
        FinderTest(code="from .src import app1", level=1, module='src', name='app1'),
        FinderTest(code="from ..src import app1", level=2, module='src', name='app1'),
        FinderTest(code="from ..src.app1 import main", level=2, module='src.app1', name='main'),
        FinderTest(code="from . import app1", level=1, module=None, name='app1'),
        FinderTest(code="from .. import app1", level=2, module=None, name='app1'),
        FinderTest(code="# import app1", level=0, module=None, name=None),
        FinderTest(code="'''import app1'''", level=0, module=None, name=None),
        FinderTest(code="from .. import *", level=2, module=None, name="*", ),
    ]
    for exmp in tests_set:
        data = ast_parser_imports(source_code_in=exmp.code)
        print(f"\t{data},")
        assert isinstance(data, list), f'Не получен список импортов для: {exmp.code}'
        for res in data:
            assert res.level == exmp.level
            assert res.module == exmp.module
            assert res.name == exmp.name


if __name__ == '__main__':
    # test_ast_parser_imports()
    # post импорты просто делятся на их количество и дублируют модуль откуда они были взяты
    print(ast_parser_imports(source_code_in='from main import app1, app2'))
