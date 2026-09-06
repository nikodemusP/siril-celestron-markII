from dataclasses import dataclass
import os
from pathlib import Path
import yaml
from sirilpy import LogColor

class config:

    def __init__(self, siril):
        self.siril = siril
        self.workDir = siril.get_siril_wd()
        self.config_Dir = siril.get_siril_userdatadir()

    def readProjectConfig(self):
        self.siril.log(f"read project config", LogColor.GREEN)
        config_file = Path(self.workDir) / "config.yaml"
        config = {}
        if not config_file.exists():
            config["siril"] = {"work_dir": self.workDir, "files_sorted": False}
            self.siril.log("Create project file", LogColor.GREEN)
            self.storeProjectConfig(config)
            return config
        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
                self.siril.log("Configuration loaded successfully.", LogColor.GREEN)
                return config
        except Exception as e:
            self.siril.log(f"Error reading configuration file: {str(e)}", LogColor.RED)
            return None

    def readPresetConfig(self):
        self.siril.log(f"read preset config", LogColor.GREEN)
        presets_file = Path(self.config_Dir) / "origin_m2_presets.yaml"
        if not presets_file.exists():
            self.siril.log("Presets file not found: orgin_m2_presets.yaml", LogColor.RED)
            return None
        try:
            with open(presets_file, "r") as f:
                presets = yaml.safe_load(f)
                self.siril.log("Presets loaded successfully.", LogColor.GREEN)
                return presets
        except Exception as e:
            self.siril.log(f"Error reading presets file: {str(e)}", LogColor.RED)
            return None
        
    def storeProjectConfig(self,config):
        config_file = Path(self.workDir) / "config.yaml"
        try:
            with open(config_file, "w") as f:
                yaml.dump(config, f)
                self.siril.log("Configuration saved successfully.", LogColor.GREEN)
        except Exception as e:
            self.siril.log(f"Error saving configuration file: {str(e)}", LogColor.RED)

    def storePresets(self, config):
        presets_file = Path(self.config_Dir) / "origin_m2_presets.yaml"
        try:
            with open(presets_file, "w") as f:
                yaml.dump(config, f)
                self.siril.log("Configuration saved successfully.", LogColor.GREEN)
        except Exception as e:
            self.siril.log(f"Error saving configuration file: {str(e)}", LogColor.RED)
