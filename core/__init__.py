from dataclasses import dataclass, field
from typing import Any
from pathlib import Path

TOML_FILE_NAME = 'pyproject.toml'


@dataclass
class Status:
    success: bool
    message: str | None = None
    data: Any = None

    def __str__(self):
        return f"status: {self.success} | message: {self.message}"

    def __repr__(self):
        return f"status: {self.success} | message: {self.message}"


@dataclass
class ProjectInfo:
    name: str
    root_dir: Path
    src_dir: Path
    depends: list[str]
    workspaces: list[str]


from typing import Callable


@dataclass
class Command:
    description: str
    parametrs: tuple
    cmd: Callable[[], None] | Callable[[str], None] | Callable[[set], bool]

    def __str__(self):
        return f"name : {self.description} | parameters : {self.parametrs}"


@dataclass
class Package:
    name: str
    local_path: Path
    is_installed: bool
    dependencies: list[str]
    package_connect: Command
    package_disconnect: Command

    # add_depends: Command
    # remove_depends: Command
    # is_depends_in_package: Command
    # is_depends_workspace: Command
    # related_files: list[Path] = field(default_factory=list)  # заполняется во внешнем модуле

    def __str__(self):
        return f"name : {self.name} | is_installed : {self.is_installed} | dependencies : {self.dependencies}"
