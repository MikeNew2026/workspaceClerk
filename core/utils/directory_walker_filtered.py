from pathlib import Path
from typing import Iterator


def directory_walker_filtered(
        root_path_in: Path,
        dirs_filter: set | None = None,
        dirs_filter_exclude: bool = False,
        extensions_filter: set[str] | None = None,
        extensions_filter_exclude: bool = False,
) -> Iterator[Path]:
    """
    Обходчик директории, с поиском файлов. Есть фильтрация по файлам и расширениями с инверсией.

    :param root_path_in: корневой путь
    :param dirs_filter: по каким папкам делать обход (или какие файлы исключить см.1 dirs_filter_exclude)
    :param dirs_filter_exclude: dirs_filter инвертирован с include на exclude (то есть указанные папки будут игнорироваться)
    :param extensions_filter: какие расширения должны быть у файлов? (или наоборот какие не должны быть если стоит extensions_filter_exclude)
    :param extensions_filter_exclude: инверсия extensions_filter (исключая расширения указанные в extension_filter)

    :return: генератор с найденными файлами
    """
    if not root_path_in.exists():
        raise FileNotFoundError(f'директория `{root_path_in}` не существует.')

    dirs_filter = dirs_filter if dirs_filter is not None else set()
    extensions_filter = extensions_filter if extensions_filter is not None else set()

    for root, dirs, files in root_path_in.walk():

        if dirs_filter:  # если подключена фильтрация папок (есть dirs_filter)
            if dirs_filter_exclude:  # включая папки
                dirs[:] = [Path(d) for d in dirs if d not in dirs_filter]
            elif not dirs_filter_exclude:  # исключая папки
                dirs[:] = [Path(d) for d in dirs if d in dirs_filter]

        for file in files:

            # если есть фильтр расширений
            if extensions_filter:
                if not extensions_filter_exclude and not file.endswith(tuple(extensions_filter)):
                    continue
                elif extensions_filter_exclude and file.endswith(tuple(extensions_filter)):
                    continue

            yield root / file


if __name__ == '__main__':
    src_path = Path(__file__).parent / 'src'
    result = directory_walker_filtered(
        root_path_in=src_path,
        dirs_filter={'.egg-info', '__pycache__'},
        dirs_filter_exclude=True,
        extensions_filter={'.py'},
        # extensions_filter_exclude=True,
    )

    for f in result:
        print(f)
