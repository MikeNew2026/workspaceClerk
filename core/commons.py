import subprocess
import platform


def run_cmd(command, cwd, waiting_subprocess: bool = False) -> subprocess.CompletedProcess:
    """

    :param command: исполняемая команда например "uv sync"
    :param cwd: путь от имени которой исполняется команда
    :param waiting_subprocess: ожидать ли завершения результата (для тестирования)
    :return: None
    """
    encoding = 'cp866' if 'windows' in platform.system().lower() else 'utf-8'
    if not waiting_subprocess and 'windows' in platform.system().lower():
        # для windows запуск особый (так как сессия зависает)
        command = f'start "UV Setup" cmd /c "{command}"'
        res = subprocess.run(command, shell=True, cwd=cwd, text=True, capture_output=True, encoding=encoding)
        return res
    else:  # для linux /  macOS
        res = subprocess.run(command, shell=True, cwd=cwd, text=True, capture_output=True, encoding=encoding)
        return res
