from abc import abstractmethod
from sirilpy import LogColor
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
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

class plugin():
    """Abstract Base Class for Plugins."""

    def __init__(self, siril, config):
        self.siril = siril
        self.plugin_name = self.get_plugin_name()
        self.title = self.get_title_name()
        siril.log(f"setup plugin: {self.plugin_name}", LogColor.GREEN)
        self._config = (config.get(self.plugin_name, {}) or {})

    def _create_widget(self):
        """everything needed for the widget."""
        group_section = QGroupBox(self.title)
        group_section.setStyleSheet("QGroupBox { font-weight: bold; }")
        group_layout = QHBoxLayout(group_section)
        group_layout.setSpacing(15)
        group_layout.setContentsMargins(10, 12, 10, 10)

        self.create_widget(group_layout)

        group_layout.addStretch() 
        button_row = QHBoxLayout()
        button_row.addStretch()  
        process_button = QPushButton("Process")
        process_button.setMinimumWidth(120)
        process_button.clicked.connect(self.process)
        button_row.addWidget(process_button)
        group_layout.addLayout(button_row)
        return group_section


    @abstractmethod
    def get_plugin_name(self):
        """Return the plugin name."""
        pass

    @abstractmethod
    def get_title_name(self):
        """Return the title name."""
        pass

    @abstractmethod
    def create_widget(self, group_layout):
        """everything needed for the widget."""
        pass

    @abstractmethod
    def process(self):
        """everything needed for the processing."""
        pass

    def get_group_section(self):
        return self.group_section

    def seril(self):
        return self.siril

    def get_siril_wd(self):
        return self.siril.get_siril_wd()
    
    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value

    