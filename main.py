import tomli_w
import tomllib
from pathlib import Path
import subprocess

root_path: None | Path = None

"""
Простой модуль для установки / демонтажа пакетов. 
В основе используется uv (требуется подключение к нему).
"""


def write_toml(toml_path, data):
    if not toml_path.exists():
        raise FileNotFoundError(f'Файл с .toml не найден `{toml_path}`')
    with open(toml_path, 'wb') as f:
        tomli_w.dump(data, f)

    return data


def read_toml(toml_path):
    if not toml_path.exists():
        raise FileNotFoundError(f'Файл с .toml не найден `{toml_path}`')
    with open(toml_path, 'rb') as f:
        data = tomllib.load(f)
    return data


def create_package(project_name: str):
    print(123)
    if project_name == '':
        print(f'❌ Название проекта не может быть пустым.')
        return
    if (root_path / project_name).exists():
        print(f'❌ Проект `{project_name}` уже существует.')
        return
    project_path = root_path / project_name
    project_path.mkdir(exist_ok=True)
    subprocess.run('uv init', cwd=project_path, capture_output=True)
    subprocess.run('uv sync', cwd=root_path, capture_output=True)


main_menu = [
    {
        'name': 'добавить depend',
        'cmd': lambda depends: subprocess.run(f'uv add {depends}', cwd=root_path, capture_output=True),
        'parameters': ['(добавляемые зависимости через пробел)']
    },
    {
        'name': 'удалить depend',
        'cmd': lambda depends: subprocess.run(f'uv remove {depends}', cwd=root_path, capture_output=True),
        'parameters': ['(удаляемые зависимости через пробел)']
    },
    {
        'name': 'создать новый пакет',
        'cmd': lambda project_name: create_package(project_name),
        'parameters': ['(название пакета)']
    },
    {
        'name': 'список пакетов',
        'cmd': lambda: packages_menu(),
        'parameters': []
    },
]


def make_add_cmd(pkg_name, path):
    def func():
        subprocess.run(f'uv add ./{pkg_name}', cwd=path, capture_output=True)
        subprocess.run('uv sync', cwd=root_path, capture_output=True)

    return lambda: func()


def make_remove_cmd(pkg_name, path):
    def func():
        data = read_toml(toml_path=path / 'pyproject.toml')
        data['tool']['uv']['workspace']['members'].remove(pkg_name)
        write_toml(toml_path=path / 'pyproject.toml', data=data)
        subprocess.run(f'uv remove {pkg_name}', cwd=path, capture_output=True)
        subprocess.run('uv sync', cwd=root_path, capture_output=True)

    return lambda: func()


def make_depends_add(pkg_name, path):
    def func(depend):
        subprocess.run(f'uv add {depend}', cwd=path / pkg_name, capture_output=True)
        subprocess.run('uv sync', cwd=root_path, capture_output=True)

    return lambda depend: func(depend)


def make_depends_remove(pkg_name, path):
    def func(depend):
        subprocess.run(f'uv remove {depend}', cwd=path / pkg_name, capture_output=True)
        subprocess.run('uv sync', cwd=root_path, capture_output=True)

    return lambda depend: func(depend)


def scan_packages():
    packages_list = []

    # поиск пакетов
    for path in root_path.iterdir():
        toml_path = path / 'pyproject.toml'
        if path.is_dir() and toml_path.exists():
            # установленные пакеты получаются из pyproject.dependencies
            packages_installed = read_toml(toml_path=root_path / 'pyproject.toml')
            packages_installed = packages_installed['project']['dependencies']

            name = path.parts[-1]
            packages_list.append({
                'name': name,
                'is_installed': path.parts[-1].lower() in packages_installed,
                'dependencies': read_toml(toml_path)['project']['dependencies'],
                'commands': [
                    {'name': 'подключить пакет',  # вот здресь  нужно расширить функцию
                     'cmd': make_add_cmd(name, path=root_path),
                     'parameters': [],
                     },
                    {'name': 'отключить пакет',
                     'cmd': make_remove_cmd(name, path=root_path),
                     'parameters': [],
                     },
                    {'name': 'установить depends в пакет',
                     'cmd': make_depends_add(pkg_name=name, path=root_path),
                     'parameters': ['(устанавливаемые зависимости через пробел)'],
                     },
                    {'name': 'удалить depends из пакета',
                     'cmd': make_depends_remove(pkg_name=name, path=root_path),
                     'parameters': ['(удаляемые зависимости через пробел)'],
                     },
                ]

            })

    return packages_list


"""
КОНСОЛЬНАЯ УТИЛИТА:
"""


def packages_command_menu(package):
    print(f'-' * 50)
    print('Команды пакетов')
    print(f'Пакет {package["name"]}:')
    while True:
        for i, cmd in enumerate(package['commands']):
            print(f'\t{i} {cmd["name"]}')

        # запуск действия
        try:
            user_inp = input(f'>_')
            if user_inp == '':
                return

            user_inp = int(user_inp)

            parameters = package['commands'][user_inp]['parameters']
            if parameters:
                parameters = input(f'Введите параметры ({parameters}):\n>_')
                package['commands'][user_inp]['cmd'](parameters)
            else:
                package['commands'][user_inp]['cmd']()
            print(f'✔ Выполнено.')

        except Exception as err:  # noqa
            print(err)
            return

        # После каждой команды обязательно делать uv sync (чтобы библиотеки из неподключенных пакетов удалялись из основного)


def packages_menu():
    print(f'-' * 50)
    print('Список пакетов')
    while True:
        # Внешнее меню с выбором пакетов
        packages = scan_packages()
        for i, pack in enumerate(packages):
            print(f"{i}. {pack['name']} | install : {pack['is_installed']} | dependencies: {pack["dependencies"]}")

        # выбор действия с пакетом
        try:
            select_pack = input(f'>_')

            if select_pack == '':
                return

            packages_command_menu(package=packages[int(select_pack)])

        except Exception:  # noqa
            pass


def start(root_dir):
    global root_path
    root_path = root_dir
    while True:
        data = read_toml(toml_path=root_path / 'pyproject.toml')
        print(f'-' * 50)
        print(f'Главное меню проекта:')
        print(f'Проект: {data['project']['name']}')
        print(f"Зависимости {data['project']['dependencies']}")
        for i, com in enumerate(main_menu):
            print(f"\t{i}. {com['name']}")
        select_menu = input(f'>_')
        if select_menu == '':
            break

        try:
            select_menu = int(select_menu)

            if main_menu[select_menu]['parameters']:
                parameters = input(f"Нужно ввести параметры ({main_menu[select_menu]['parameters']}) :\n>_")
                main_menu[select_menu]['cmd'](parameters)
            else:
                main_menu[select_menu]['cmd']()
            print(f'✔ Выполнено.')
        except Exception:  # noqa
            pass


if __name__ == '__main__':
    from pathlib import Path

    root_dir_path = Path(__file__).parent
    start(root_dir=root_dir_path)
