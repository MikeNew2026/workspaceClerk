from pathlib import Path
from core.commons import run_cmd
from core.utils.manager_toml import TomlManager
from core import Status, TOML_FILE_NAME, Package, Command
import os
import shutil


class ManagerPackages:

    def __init__(self, root_path_in: Path, src_path_in: Path, waiting_subprocess: bool = False):
        self._root_path = root_path_in
        self._src_path = src_path_in
        self._src_local_path = self._src_path.relative_to(self._root_path)
        self._waiting_subprocess = waiting_subprocess  # ожидание завершения работы suprocess

    def _is_package_installed(self, pckg_name: str) -> bool:
        data = TomlManager(toml_path=self._root_path / TOML_FILE_NAME)
        return data.is_package_in_workspaces(package=str(self._src_local_path / pckg_name))

    def _is_package_exists(self, pkg_name: str) -> Status:
        # Проверки существования пакета
        if self._is_package_installed(pckg_name=pkg_name):
            return Status(
                success=False,
                message=f'⚠ Пакет `{self._src_local_path / pkg_name}` уже существует, и установлен.'
            )

        if pkg_name == '':
            return Status(
                success=False,
                message=f'⚠ Название пакета не может быть пустым.'
            )

        if (self._src_path / pkg_name / TOML_FILE_NAME).exists():
            return Status(
                success=False,
                message=f'⚠ Пакет `{self._src_local_path / pkg_name}` уже существует.'
            )
        return Status(success=True, message=f'✔ Пакет не существует. Проверка выполнена')

    def package_create(self, pkg_name: str) -> Status:
        """Создание нового пакета"""

        # проверка существует ли уже пакет
        status = self._is_package_exists(pkg_name)
        if not status.success:
            return status

        # путь к пакету
        package_path = self._src_path / pkg_name
        package_path_inner_src = package_path / 'src' / pkg_name

        # Создание каталога с пакетом, с вложенной директорией src
        project_path = package_path / 'src' / pkg_name
        project_path.mkdir(exist_ok=True, parents=True)

        # инициализация проекта и uv синхронизация
        cmd = f'uv init && uv sync'
        run_cmd(command=cmd, cwd=package_path, waiting_subprocess=self._waiting_subprocess)

        # создание файла main.py в package/src/package
        with open(file=package_path_inner_src / 'main.py', mode='w', encoding='utf8') as f:
            f.write('if __name__ == "__main__":\n\tpass')

        # создание файла __init__.py в package/src/package
        with open(file=package_path_inner_src / '__init__.py', mode='w', encoding='utf8') as f:
            f.write('')

        # удаление python файла из корня пакета
        if (package_path / 'main.py').exists():
            os.remove(package_path / 'main.py')

        # удаление папки egg-info (она не нужна)
        if (package_path / 'src' / f'{pkg_name.lower()}.egg-info').exists():
            shutil.rmtree(package_path / 'src' / f'{pkg_name.lower()}.egg-info')

        # очистить workspace в toml после создания пакета
        toml_session = TomlManager(self._root_path / TOML_FILE_NAME)
        toml_session.workspaces_remove(depend=pkg_name)
        toml_session.write_toml()

        return Status(success=True, message=f'✔ Пакет `{package_path}` создан')

    def get_packages_list(self) -> tuple[Status, None | list[Package]]:

        packages_list = []

        if not self._src_path.exists():
            return (
                Status(
                    success=False,
                    message=f'⚠ Не найдена директория с пакетами по пути `{self._src_path}`'
                ),
                None)

        for path in self._src_path.iterdir():
            if path.is_dir() and (path / TOML_FILE_NAME).exists():
                data = TomlManager(path / TOML_FILE_NAME)

                package = Package(
                    name=data.name,
                    dependencies=data.depends,
                    local_path=self._src_path / data.name,
                    is_installed=False,
                    package_connect=Command(
                        cmd=self.make_packages_connect_func(data.name),
                        description='подключить пакет',
                        parametrs=(),
                    ),
                    package_disconnect=Command(
                        cmd=self.make_packages_disconnect_func(data.name),
                        description='отключить пакет',
                        parametrs=(),
                    )
                )
                packages_list.append(package)

        return (
            Status(
                success=True,
                message=f'✔ Информация о пакетах получена.'
            ),
            packages_list
        )

    def make_packages_connect_func(self, pkg_name):
        def func():
            cmd = f"uv add {self._src_path / pkg_name} &&  uv  sync"
            run_cmd(command=cmd, cwd=self._root_path, waiting_subprocess=self._waiting_subprocess)

        return lambda: func()

    def make_packages_disconnect_func(self, pkg_name):
        def func():
            # удаление пакета в главном toml (очистка его в depends, workspaces, sources)
            toml_session = TomlManager(toml_path=self._root_path / TOML_FILE_NAME)
            toml_session.depends_remove(depend=pkg_name)
            toml_session.workspaces_remove(depend=pkg_name)
            toml_session.sources_remove(depend=pkg_name)
            toml_session.write_toml()

            run_cmd(command=f'uv remove {pkg_name}', cwd=self._root_path, waiting_subprocess=self._waiting_subprocess)
            run_cmd(command='uv sync', cwd=self._root_path, waiting_subprocess=self._waiting_subprocess)

        return lambda: func()


if __name__ == '__main__':
    root_path = Path(r'C:\Users\MikeCoder\Desktop\test')
    src_path = Path(r'C:\Users\MikeCoder\Desktop\test\src')
    pm = ManagerPackages(
        root_path_in=root_path,
        src_path_in=src_path,
    )
    # print(pm.package_create(pkg_name='app1'))
    # print(pm.package_create(pkg_name='app2'))
    pm.get_packages_list()[1][0].package_connect.cmd()
    # pm.get_packages_list()[1][0].package_disconnect.cmd()
