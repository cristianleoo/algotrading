# import libraries
import importlib
import subprocess

class imp_inst():
    def import_or_install(package):
            try:
                importlib.import_module(package)
                print(f'{package} is already installed')
            except ImportError:
                print(f'{package} is not installed, installing now...')
                subprocess.check_call(['pip', 'install', package])
                print(f'{package} has been installed')