from pathlib import Path
from core.manager_project import ManagerProject
from core.manager_packages import ManagerPackages
from core import Status, ProjectInfo, TOML_FILE_NAME
from core.utils.manager_toml import TomlManager


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

    def package_create(self, pkg_name: str):
        status = self.packages_manager.package_create(pkg_name=pkg_name)
        return status


if __name__ == '__main__':
    root_path = Path(r'C:\Users\MikeCoder\Desktop\test')
    src_path = Path(r'C:\Users\MikeCoder\Desktop\test\src')
    wc = WorkspaceClerk(root_path_in=root_path, src_path_in=src_path)
    print(wc.project_depends_add(depends={'python-dotenv'}))
    print(wc.package_create(pkg_name='APP1'))
    print(wc.package_create(pkg_name='APP2'))

    # print(wc.project_depends_remove(depends={'python-dotenv'}))
    print(wc.project_get_info())
