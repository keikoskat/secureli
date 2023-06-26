from pathlib import Path
from typing import Optional
import yaml

from pydantic import BaseModel


class SecureliConfig(BaseModel):
    overall_language: Optional[str]
    version_installed: Optional[str]


class SecureliConfigRepository:
    """Save and retrieve the SeCureLI configuration"""

    def save(self, folder_path: Path, secureli_config: SecureliConfig):
        """
        Save the specified configuration to the .secureli folder
        :param secureli_config: The populated configuration to save
        """
        secureli_folder_path = self._initialize_secureli_directory(folder_path)
        secureli_config_path = secureli_folder_path / "repo-config.yaml"
        with open(secureli_config_path, "w") as f:
            yaml.dump(secureli_config.dict(), f)

    def load(self, folder_path: Path) -> SecureliConfig:
        """
        Load the SeCureLI config from the expected configuration file path or return a new
        configuration object, capable of being modified and saved via the `save` method
        """
        secureli_folder_path = self._initialize_secureli_directory(folder_path)
        secureli_config_path = Path(secureli_folder_path / "repo-config.yaml")
        print("***************")
        print(secureli_config_path)
        if not secureli_config_path.exists():
            print("NOT EXISTS")
            return SecureliConfig()

        with open(secureli_config_path, "r") as f:
            print("EXISTS")
            data = yaml.safe_load(f)
            return SecureliConfig.parse_obj(data)

    def _initialize_secureli_directory(self, folder_path: Path):
        """
        Creates the .secureli folder within the current directory if needed.
        :return: The folder path of the .secureli folder that either exists or was just created.
        """
        secureli_folder_path = Path(folder_path / ".secureli")
        print("$$$$$$$$$")
        print(secureli_folder_path)
        secureli_folder_path.mkdir(parents=True, exist_ok=True)
        return secureli_folder_path
