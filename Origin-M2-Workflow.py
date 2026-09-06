import os
from pathlib import Path
import sys
import math
import shutil
import time
from datetime import datetime
from tkinter import font
import originM2lib
import sirilpy as s
import originM2Plugins

s.ensure_installed("PyQt6", "numpy", "astropy")

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QCheckBox,
    QDoubleSpinBox,
    QComboBox,
    QGroupBox,
    QMessageBox,
    QFileDialog,
    QSpinBox,
    QScrollArea,
    QProgressBar,
)
from sirilpy import LogColor, NoImageError
from PyQt6.QtCore import pyqtSlot as Slot, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QShortcut, QKeySequence

APP_NAME = "Origin-Mark2 Processing"
VERSION = "0.1.0"

PLUGIN_CONFIG = [
    {"keyName": "O2SortFiles", "class": "OriginMark2FileSorter", "enabled": True}
]

class ProcessingInterface(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} - v{VERSION}")

        self.siril = self.connect_to_siril()
        self.siril.log(f"read config", LogColor.GREEN)
        self.config = originM2lib.config(self.siril)
        self.project_config = self.config.readProjectConfig()
        self.presets = self.config.readPresetConfig()
        self.workDir = self.siril.get_siril_wd()
        # Load the plugins
        self.siril.log(f"load plugins", LogColor.GREEN)
        self.plugins = {}
        for plugin_info in PLUGIN_CONFIG:
            if plugin_info.get("enabled", True):
                key_name = plugin_info["keyName"]
                class_name  = plugin_info["class"]
                try:
                    module = __import__(f"originM2Plugins.{class_name}", fromlist=[class_name])
                    plugin_class = getattr(module, class_name)
                    plugin_instance = plugin_class(self.siril, self.project_config)
                    self.plugins[key_name] = plugin_instance
                    self.siril.log(f"Loaded plugin: {plugin_instance.get_plugin_name()}", LogColor.GREEN)
                except Exception as e:
                    self.siril.log(f"Error loading plugin {class_name} from originM2Plugins.{class_name}: {e}", LogColor.RED)

        self.create_widget()

        self.initialization_successful = True


    def close_dialog(self):
        self.siril.disconnect()
        self.close()

    def connect_to_siril(self):
        try:
            siril = s.SirilInterface()
            siril.connect()
            siril.log("Connected to Siril", LogColor.GREEN)
            return siril
        except Exception as e:
            siril.log("Failed to connect to Siril", LogColor.RED)
            self.close_dialog()

    def create_widget(self):
        """Creates the UI widgets."""
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Set default window size (larger by default)
        self.resize(950, 850)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        main_layout.addWidget(scroll_area)

        # Create content widget for scroll area
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(12, 8, 12, 12)
        content_layout.setSpacing(10)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # keep things packed at top

        info_box = QFrame()
        info_box.setFrameShape(QFrame.Shape.StyledPanel)
        info_layout = QVBoxLayout(info_box)
        cwd_label = QLabel(f"Current Working Directory: {self.workDir}")
        cwd_label.setWordWrap(True)
        info_layout.addWidget(cwd_label)

        content_layout.addWidget(info_box)
    
        for plugin_info in PLUGIN_CONFIG:
            plugin_instance = self.plugins.get(plugin_info["keyName"])
            if plugin_instance:
                content_layout.addWidget(plugin_instance._create_widget())

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(10)  # Make it slim
        # Remove border and make it span full width
        main_layout.addWidget(self.progress_bar)

        # Buttons section
        button_layout = self._create_buttons_layout()

        # Wrap button layout in a widget to easily disable/enable all buttons
        self.buttons_widget = QWidget()
        self.buttons_widget.setLayout(button_layout)
        # Add buttons to bottom of main layout (after scrollable area)
        main_layout.addWidget(self.buttons_widget)

    def _create_buttons_layout(self):
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(12, 10, 12, 12)
        button_layout.setSpacing(8)

#        help_button = QPushButton("Help")
#        help_button.setMinimumWidth(50)
#        help_button.setMinimumHeight(35)
#        help_button.setToolTip("Show help information and frequently asked questions")
#        help_button.clicked.connect(self.show_help)
#        button_layout.addWidget(help_button)

        save_presets_button = QPushButton("Save Presets")
        save_presets_button.setMinimumWidth(80)
        save_presets_button.setMinimumHeight(35)
        save_presets_button.setToolTip(
            'Save current settings to a "naztronomy_smart_scope_presets.json" file in the presets directory'
        )
#        save_presets_button.clicked.connect(self.save_presets)
        button_layout.addWidget(save_presets_button)

        load_presets_button = QPushButton("Load Presets")
        load_presets_button.setMinimumWidth(80)
        load_presets_button.setMinimumHeight(35)
        load_presets_button.setToolTip(
            'Load previously saved presets. If "presets/naztronomy_smart_scope_presets.json" exists, it will load first, otherwise it\'ll prompt you to find a proper .json file.'
        )
#        load_presets_button.clicked.connect(self.load_presets)
        button_layout.addWidget(load_presets_button)

 #       button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.setMinimumWidth(100)
        close_button.setMinimumHeight(35)
        close_button.setStyleSheet(
            "QPushButton { background-color: #c70306; color: white; font-weight: bold; border-radius: 4px; } QPushButton:hover { background-color: #fc3437; }"
        )
        close_button.clicked.connect(self.close_dialog)
        button_layout.addWidget(close_button)

        button_layout.addSpacing(10)

        self.run_button = QPushButton("Run")
        self.run_button.setMinimumWidth(100)
        self.run_button.setMinimumHeight(35)
        self.run_button.setStyleSheet(
            "QPushButton { background-color: #0078cc; color: white; font-weight: bold; border-radius: 4px; } QPushButton:hover { background-color: #33abff; }"
        )
#        self.run_button.clicked.connect(self.on_run_clicked)
        button_layout.addWidget(self.run_button)

        return button_layout

def main():
    try:
        app = QApplication(sys.argv)
        window = ProcessingInterface()

        # Only show window if initialization was successful
        if window.initialization_successful:
            window.show()
            sys.exit(app.exec())
        else:
            # User canceled during initialization - exit gracefully
            sys.exit(0)
    except Exception as e:
        print(f"Error initializing application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
