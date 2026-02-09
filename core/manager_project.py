from pathlib import Path
from core.commons import run_cmd
from core.utils.manager_toml import TomlManager
from core import Status, ProjectInfo, TOML_FILE_NAME


class ManagerProject:

    def __init__(self, root_path_in: Path, src_path_in: Path, waiting_subprocess: bool = False):
        self._root_path = root_path_in
        self._src_path = src_path_in
        self._src_local_path = self._src_path.relative_to(self._root_path)
        self._waiting_subprocess = waiting_subprocess  # ожидание завершения работы suprocess

    def project_init(self) -> Status:
        cmd = "uv --version"
        res = run_cmd(
            command=cmd,
            cwd=self._root_path,
            waiting_subprocess=True
        )
        if res.returncode != 0:
            raise RuntimeError(f'❌ Системная ошибка,(скорее всего не найден uv): {res.stdout} {res.stderr}')

        if not (self._root_path / TOML_FILE_NAME).exists():
            cmd = "uv init && uv sync"
            res = run_cmd(command=cmd, cwd=self._root_path, waiting_subprocess=self._waiting_subprocess)
            if res.returncode != 0:
                return Status(success=False, message=f'⚠ Проект не был инициализирован: {res.stdout} {res.stderr}')
        return Status(success=True, message='✔ Проект инициализирован')

    def project_depend_add(self, depend: str) -> Status:
        """
        Подключение зависимостей например "uv add requests"
        :param depend: зависимость в виде строки например "python-dotenv"
        :return:
        """

        # проверка что зависимость не установлена уже
        toml_session = TomlManager(toml_path=self._root_path / TOML_FILE_NAME)
        if toml_session.is_package_in_dependencies(package=depend):  # проверка что библиотека не существует
            return Status(
                success=False,
                message=f'⚠ Зависимость `{depend}` не была установлена так как уже существует.'
            )

        cmd = f"uv add {depend}"
        res = run_cmd(command=cmd, cwd=self._root_path, waiting_subprocess=self._waiting_subprocess)
        if res.returncode != 0:
            return Status(
                success=False,
                message=f'⚠ Зависимость `{depend}` не была установлена: {res.stdout} {res.stderr}'
            )

        return Status(
            success=True,
            message=f'✔ Зависимость `{depend}` была установлена в корень проекта.'
        )

    def project_depend_remove(self, depend: str) -> Status:
        """
        Отключение зависимостей например "uv add requests"
        :param depend: зависимость в виде строки например "python-dotenv"
        :return:
        """
        # проверка что зависимость существует в проекте
        toml_session = TomlManager(toml_path=self._root_path / TOML_FILE_NAME)
        if not toml_session.is_package_in_dependencies(package=depend):
            return Status(
                success=False,
                message=f'⚠ Зависимость `{depend}` не была удалена так как отсутствует в проекте.'
            )

        cmd = f"uv remove {depend}"
        res = run_cmd(command=cmd, cwd=self._root_path, waiting_subprocess=self._waiting_subprocess)
        if res.returncode != 0:
            return Status(
                success=False,
                message=f'⚠ Зависимость `{depend}` не была удалена: {res.stdout} {res.stderr}'
            )

        return Status(
            success=True,
            message=f'✔ Зависимость `{depend}` была удалена из корня проекта.'
        )

    def project_get_info(self) -> tuple[Status, ProjectInfo | None]:
        # очистить workspace в toml после создания пакета
        try:
            data = TomlManager(self._root_path / TOML_FILE_NAME)

            return (
                Status(
                    success=True,
                    message=f'✔ Информация о проекте получена.'
                ),
                ProjectInfo(
                    name=data.name,
                    root_dir=self._root_path,
                    src_dir=self._src_path,
                    depends=data.depends,
                    workspaces=data.workspaces,
                )
            )

        except Exception as err:
            return (
                Status(
                    success=False,
                    message=f'⚠ Не удалось получить информацию о проекте из `{self._root_path / TOML_FILE_NAME}`\n{err}'
                ),
                None
            )


if __name__ == '__main__':
    root_path = Path(r'C:\Users\MikeCoder\Desktop\test')
    src_path = Path(r'C:\Users\MikeCoder\Desktop\test\src')
    pm = ManagerProject(
        root_path_in=root_path,
        src_path_in=src_path,
    )
    # print(pm.project_init())
    print(pm.project_get_info())
    # print(pm.project_depend_add(depend='python-dotenv'))
    # print(pm.project_depend_remove(depend='aiosqlite'))
