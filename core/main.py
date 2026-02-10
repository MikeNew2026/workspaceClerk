from pathlib import Path
from core.manager_project import ManagerProject
from core.manager_packages import ManagerPackages
from core.models import Status, ProjectInfo
from typing import Generator
from core.models import Package


class WorkspaceClerk:
    def __init__(self, root_path_in: Path, src_path_in: Path, waiting_subprocess: bool = False):
        self._root_path = root_path_in
        self._src_path = src_path_in
        self.project_manager = ManagerProject(
            root_path_in=root_path_in,
            src_path_in=src_path_in,
            waiting_subprocess=waiting_subprocess
        )
        self.packages_manager = ManagerPackages(
            root_path_in=root_path_in,
            src_path_in=src_path_in,
            waiting_subprocess=waiting_subprocess
        )
        self.project_init()

    def project_init(self) -> Status:
        status = self.project_manager.project_init()
        if not status.success:
            raise Exception(f'❌ Пакет не был инициализирован -> {status.message}')
        return status

    def project_get_info(self) -> tuple[Status, ProjectInfo | None]:
        status, project_info = self.project_manager.project_get_info()
        return status, project_info

    def project_depends_add(self, depends: set):
        status_list = []
        for dep in depends:
            status = self.project_manager.project_depend_add(depend=dep)
            status_list.append(status)
        return status_list

    def project_depends_remove(self, depends: set):
        status_list = []
        for dep in depends:
            status = self.project_manager.project_depend_remove(depend=dep)
            status_list.append(status)
        return status_list

    def packages_list(self,
                      offset: int = 0, limit: int = 100,
                      filter_packages: set | None = None, filter_exclude: bool = False,
                      ) -> Generator[Package, Status, Status]:

        packages_data: Generator[Package, Status, Status] = self.packages_manager.packages_get_list()
        filter_packages = {package.lower() for package in filter_packages} if filter_packages else None

        # если packages_list не был получен и вернулся статус
        if isinstance(packages_data, Status):
            return packages_data  # возвращение статуса Status

        counter = 0

        for pack in packages_data:
            counter += 1

            # обычная пагинация
            if filter_packages is None and offset < counter <= offset + limit:
                yield pack

            # фильтрация по пакетам (поиск конкретных)
            elif filter_packages is not None:
                if not filter_exclude and pack.name in filter_packages:
                    yield pack

                elif filter_exclude and pack.name not in filter_packages:
                    yield pack

            if counter > offset + limit:
                break

        return Status(success=True, message='✔ Все пакеты просмотрены.')

    @staticmethod
    def _packages_apply_callback(original_query: set,
                                 packages_data: Status | Generator[Package, Status, Status],
                                 callback
                                 ):
        status_list = []
        if isinstance(packages_data, Status):
            return [packages_data]  # вернуть статус

        success_packages = []
        for package in packages_data:
            if package.name in original_query:
                success_packages.append(package.name)  # Пакеты к которым callback функция была применена

            status = callback(package)
            status_list.append(status)

        # проверка что callback функция была применена к пакету
        for i in original_query:
            if i.lower() not in success_packages:
                status_list.append(Status(
                    success=False,
                    message=f'⚠ Пакет `{i}` не существует, либо в нем отсутствует pyproject.toml. Используйте package_create(package="{i}").')
                )

        return status_list

    def packages_create(self, packages: set) -> list[Status]:
        status_list = []
        for pkg_name in packages:
            status = self.packages_manager.package_create(pkg_name=pkg_name)
            status_list.append(status)
        return status_list

    def packages_connect(self, packages: set) -> list[Status]:
        # Получить список релевантных пакетов
        packages_data = self.packages_list(
            filter_packages=packages,
            filter_exclude=False
        )

        # выполнить функцию с ними
        status_list = self._packages_apply_callback(
            original_query=packages,
            packages_data=packages_data,
            callback=lambda pack: pack.connect.cmd(),
        )

        return status_list

    def packages_connect_all(self, packages: set | None = None, exclude: bool = False) -> list[Status]:
        packages = packages if packages is not None else set()

        # Получить список релевантных пакетов
        packages_data = self.packages_list(
            filter_packages=packages,
            filter_exclude=exclude
        )

        # выполнить функцию с ними
        status_list = self._packages_apply_callback(
            original_query=packages,
            packages_data=packages_data,
            callback=lambda pack: pack.connect.cmd(),
        )

        return status_list

    def packages_disconnect(self, packages: set) -> list[Status]:
        # Получить список релевантных пакетов
        packages_data = self.packages_list(
            filter_packages=packages,
            filter_exclude=False
        )

        # выполнить функцию с ними
        status_list = self._packages_apply_callback(
            original_query=packages,
            packages_data=packages_data,
            callback=lambda pack: pack.disconnect.cmd(),
        )

        return status_list

    def packages_disconnect_all(self, packages: set | None = None, exclude: bool = False) -> list[Status]:
        packages = packages if packages is not None else set()

        # Получить список релевантных пакетов
        packages_data = self.packages_list(
            filter_packages=packages,
            filter_exclude=exclude
        )

        # выполнить функцию с ними
        status_list = self._packages_apply_callback(
            original_query=packages,
            packages_data=packages_data,
            callback=lambda pack: pack.disconnect.cmd(),
        )

        return status_list

    def packages_depends_add(self, package: str, depends: set):
        status_list = []

        # Получить список релевантных пакетов
        packages_data = self.packages_list(
            filter_packages={package},
            filter_exclude=False
        )

        for dep in depends:
            status = self._packages_apply_callback(
                original_query={package},
                packages_data=packages_data,
                callback=lambda pack: pack.depends_add.cmd(dep),
            )
            status_list.append(status)

        return status_list

    def packages_depends_remove(self, package: str, depends: set):
        status_list = []

        # Получить список релевантных пакетов
        packages_data = self.packages_list(
            filter_packages={package},
            filter_exclude=False
        )

        for dep in depends:
            status = self._packages_apply_callback(
                original_query={package},
                packages_data=packages_data,
                callback=lambda pack: pack.depends_remove.cmd(dep),
            )
            status_list.append(status)

        return status_list


if __name__ == '__main__':
    root_path = Path(r'C:\Users\MikeCoder\Desktop\test')
    src_path = Path(r'C:\Users\MikeCoder\Desktop\test\src')
    wc = WorkspaceClerk(root_path_in=root_path, src_path_in=src_path)
    # просмотр пакетов
    wc.packages_create(packages={'app1000'})

    # [print(i) for i in wc.packages_list(filter_packages={'app1', }, filter_exclude=False)]

    # [print(i) for i in wc.packages_connect(packages={'app1', })]
    # [print(i) for i in wc.packages_depends_add(package='app1', depends={'python-dotenv'})]
    # [print(i) for i in wc.packages_depends_remove(package='app1', depends={'python-dotenv'})]
    # [print(i) for i in wc.packages_disconnect_all()]
    # [print(i) for i in wc.packages_disconnect(packages={'app1', 'app2', 'app3'})]
    # [print(i) for i in wc.packages_connect_all()]
    # [print(i) for i in wc.packages_disconnect_all()]

    # [print(p) for p in wc.packages_list(filter_packages={'app1'}, filter_exclude=False)]
    # [print(st) for st in wc.packages_connect_all(packages={'APP1', }, exclude=False)]
    # [print(st) for st in wc.packages_disconnect_all(packages={'APP1', }, exclude=True)]

    # print(wc.project_depends_add(depends={'python-dotenv'}))
    # packages_order = {f"APP{i}" for i in range(1, 21)}
    # [print(st) for st in wc.packages_create(packages=packages_order)]

    # print(wc.project_depends_remove(depends={'python-dotenv'}))
    # print(wc.project_get_info())
