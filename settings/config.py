import os
import json
import yaml
from pathlib import Path
from dotenv import load_dotenv

try:
    from utils.decorators import utils
except ImportError as ie:
    exit(f'{ie} :: {Path(__file__).resolve()}')


class Config:
    def __init__(self):
        self.config_path: Path = Path(__file__).resolve().parent
        self.project_path: Path = Path(self.config_path).parent
        self.env_path: str = os.path.join(self.project_path, '.env')
        self.read_setup()
        load_dotenv(dotenv_path=self.env_path)

    def __getattr__(self, attr: str) -> str:
        return os.getenv(attr)

    @utils.exception
    def read_setup(self) -> None:
        file_path: str = os.path.join(self.config_path, 'setup.yml')
        with open(file=file_path, mode='r', encoding='utf-8') as file:
            settings: dict = yaml.safe_load(file)
            for setting in settings:
                setattr(self, setting.upper(), settings[setting])


config: Config = Config()
