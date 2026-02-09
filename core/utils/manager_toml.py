from pathlib import Path

from dataclasses import dataclass, field
import tomllib
import tomli_w


@dataclass
class TomlManager:
    toml_path: Path
    data: dict = field(default_factory=dict)
    name: str = ...
    version: str = ...
    description: str = ...
    requires_python: str = ...
    _depends: set[str] = field(default_factory=set)
    _workspaces: set[str] = field(default_factory=set)
    _sources: set[str] = field(default_factory=set)

    def __post_init__(self):  # чтение toml файла (сразу после инициализации объекта)
        try:
            with open(self.toml_path, 'rb') as f:
                data: dict = tomllib.load(f)
                self.data = data

                self.name = self.data['project']['name']
                self.version = self.data['project']['version']
                self.description = self.data['project']['description']
                self.requires_python = self.data['project']['requires-python']

                self._workspaces = set(data.get('tool', {}).get('uv', {}).get('workspace', {}).get('members', set()))
                # отделить библиотеки от пакетов
                depends = set(data.get('project', {}).get('dependencies', set()))
                for dep in depends:
                    if not self.is_package_in_workspaces(dep):
                        self._depends.add(dep)

                sources = data.get('tool', {}).get('uv', {}).get('sources', {})
                self._sources = set(sources.keys()) if sources else set()

        except FileNotFoundError:
            raise Exception(f'❌ Файл `{self.toml_path}` не найден.')
        except Exception:
            raise

    @property
    def depends(self):
        return self._depends

    def depends_add(self, depend: str):
        self._depends.add(depend)

    def depends_remove(self, depend: str):
        # удаление depends с игнорированием символов, только цифры и буквы
        for d in self._depends:
            if self._contains_alnum_suffix(d, depend):
                self._depends.remove(d)
                break

    @property
    def workspaces(self):
        return self._workspaces

    def workspaces_add(self, depend: str):
        self._workspaces.add(depend)

    def workspaces_remove(self, depend: str):
        # удаление workspace с игнорированием символов, только цифры и буквы
        depend = str(depend)
        for w in self._workspaces:
            if self._contains_alnum_suffix(w, depend):
                self._workspaces.remove(w)
                break

    @property
    def sources(self):
        return self._sources

    def sources_remove(self, depend: str):
        # удаление depends с игнорированием символов, только цифры и буквы
        for s in self._sources:
            if self._contains_alnum_suffix(s, depend):
                self._sources.remove(s)
                break

    @staticmethod
    def _contains_alnum_suffix(string: str, sub_string: str, register: bool = False) -> bool:
        """
        Проверка совпадения символьно цифрового ряда в обратном порядке (с игнорированием знаков пунктуации)
        например:
        src.app1.test in src/app1,
        так как: 1ppasrc == 1ppasrc
        :param string: строка включающая (не включающая) в себя проверяемую строку
        :param sub_string: строка которая должна быть включена
        :param register: учитывать регистр?
        :return:
        """
        if not register:
            string = string.lower()
            sub_string = sub_string.lower()
        different = (len(string) - 1) - (len(sub_string) - 1)

        for i in range(len(string) - 1, -1, -1):
            indx = i - different

            if not string[i].isalpha() and not sub_string[indx].isalpha():
                if not string[i].isdigit() and not sub_string[indx].isdigit():
                    continue

            if indx == 0:
                return True

            if string[i] != sub_string[indx]:
                return False
        return False

    def is_package_in_dependencies(self, package: str) -> bool:
        return any(pack_dep.startswith(package) for pack_dep in self._depends)

    def is_package_in_workspaces(self, package: str) -> bool:
        return any(self._contains_alnum_suffix(string=w, sub_string=package, register=False) for w in self._workspaces)

    def is_package_in_sources(self, package: str) -> bool:
        return any(self._contains_alnum_suffix(string=w, sub_string=package, register=False) for w in self._sources)

    def write_toml(self):
        """Запись toml файла"""
        data = self.data.copy()

        data.setdefault('project', {})['dependencies'] = list(self._depends)

        # запись workspace (даже если его нет в любом случае создать)
        # пересчёт uv.workspace если бы измен
        data.setdefault('tool', {})
        data['tool'].setdefault('uv', {})
        data['tool']['uv'].setdefault('workspace', {})
        data['tool']['uv']['workspace']['members'] = list(self._workspaces)

        # пересчёт uv.source если бы измен
        if data.get('tool', {}).get('uv', {}).get('sources', None):
            for key in list(data['tool']['uv']['sources'].keys()):
                if key not in self._sources:
                    del data['tool']['uv']['sources'][key]

        with open(self.toml_path, 'wb') as f:
            tomli_w.dump(data, f)


if __name__ == '__main__':
    ps = TomlManager(toml_path=Path(r'C:\Users\MikeCoder\Desktop\test\pyproject.toml'))
    # print(ps.is_package_in_sources('app1'))
    # print(ps.sources)
    ps.sources_remove(depend='app1')
    ps.write_toml()
    #     print(ps.sources)
