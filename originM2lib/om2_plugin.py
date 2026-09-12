from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from sirilpy import LogColor
from PyQt6.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QFormLayout,
    QLayout,
    QLineEdit,
    QMainWindow,
    QSizePolicy,
    QSlider,
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

@dataclass
class PluginContext:
    """defines the context of the plugin."""
    siril: Any
    config: dict

@dataclass
class PluginItem:
    """defines the widget within the plugin box."""
    kind: str                 # "checkbox" | "slider" | "int" | "float" | "text"
    key: str                  # internal key

    label: str = None         # label for the widget
    default: Any = None
    minimum: float = 0
    maximum: float = 100
    step: float = 1
    decimals: int = 2         
    tooltip: str = ""
    value: Any = None

class PluginConfigBox(QGroupBox):
    """
    Signals:
        activeChanged(bool)      -> if the box is checked/unchecked
        valueChanged(str, object) -> active on each value change of the contained widgets, emits (key, value)
        loadRequested()           -> "Load" button was clicked (only if show_load_button=True)
        processRequested()        -> "Process" button was clicked
    """

    activeChanged = pyqtSignal(bool)
    valueChanged = pyqtSignal(str, object)
    loadRequested = pyqtSignal()
    processRequested = pyqtSignal()

    def __init__(
        self,
        title: str,
        items: list[PluginItem],
        active: bool = True,
        parent: Optional[QWidget] = None,
        show_load_button: bool = True,
        show_process_button: bool = True,
        columns: int = 5,
    ):
        super().__init__(title, parent)

        # --- "active" Checkbox in the title ---
        self.setCheckable(True)
        self.setChecked(active)
        self.toggled.connect(self.activeChanged.emit)

        self._items: dict[str, PluginItem] = {item.key: item for item in items}
        self._widgets: dict[str, QWidget] = {}
        self._columns = max(1, columns)

        # Äußeres Layout: oben das Grid, unten die Buttons
        outer_layout = QVBoxLayout()
        self.setLayout(outer_layout)

        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(12)
        grid_layout.setVerticalSpacing(8)
        for col in range(self._columns):
            grid_layout.setColumnStretch(col, 1)  # alle Spalten gleich breit -> Breite / columns
        outer_layout.addLayout(grid_layout)

        row = 0
        col = 0

        for item in items:
            widget = self._build_widget(item)
            self._widgets[item.key] = widget

            if item.kind == "separator":
                # Erzwingt Sprung in die nächste Zeile, egal wie viele Spalten noch frei wären
                if col != 0:
                    row += 1
                    col = 0
                continue

            if item.kind == "checkbox":
                cell_widget = widget
            else:
                # Label + Widget nebeneinander in einer Zeile, passend zur Spaltenbreite
                cell_widget = QWidget()
                cell_hbox = QHBoxLayout(cell_widget)
                cell_hbox.setContentsMargins(0, 0, 0, 0)
                cell_hbox.setSpacing(6)
                label = QLabel(item.label)
                label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
                widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                cell_hbox.addWidget(label)
                cell_hbox.addWidget(widget, stretch=1)

            grid_layout.addWidget(cell_widget, row, col)

            col += 1
            if col >= self._columns:
                col = 0
                row += 1

        self.load_button: Optional[QPushButton] = None
        self.process_button: Optional[QPushButton] = None

        if show_load_button or show_process_button:
            self._add_buttons(outer_layout, show_load_button, show_process_button)

    # ------------------------------------------------------------------
    # buttons
    # ------------------------------------------------------------------
    def _add_buttons(
        self,
        layout: QVBoxLayout,
        show_load_button: bool,
        show_process_button: bool,
    ) -> None:
        button_row = QWidget()
        hbox = QHBoxLayout(button_row)
        hbox.setContentsMargins(0, 8, 0, 0)

        hbox.addStretch()

        if show_load_button:
            self.load_button = QPushButton("Load")
            self.load_button.clicked.connect(self.loadRequested.emit)
            hbox.addWidget(self.load_button)

        if show_process_button:
            self.process_button = QPushButton("Process")
            self.process_button.clicked.connect(self.processRequested.emit)
            hbox.addWidget(self.process_button)

        layout.addWidget(button_row)

    # ------------------------------------------------------------------
    # create widget
    # ------------------------------------------------------------------
    def _build_widget(self, item: PluginItem) -> QWidget:
        if item.kind == "separator":
            # Marker-Widget: erzeugt keinen sichtbaren Inhalt, wird gar nicht ins Grid gelegt
            w = QWidget()
            w.setFixedSize(0, 0)
            return w

        if item.kind == "checkbox":
            w = QCheckBox(item.label)
            w.setChecked(bool(item.default))
            w.setToolTip(item.tooltip)
            w.stateChanged.connect(
                lambda _state, k=item.key, box=w: self.valueChanged.emit(k, box.isChecked())
            )
            return w

        elif item.kind == "slider":
            container = QWidget()
            hbox = QHBoxLayout(container)
            hbox.setContentsMargins(0, 0, 0, 0)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(int(item.minimum))
            slider.setMaximum(int(item.maximum))
            slider.setSingleStep(int(item.step))
            slider.setValue(int(item.default or 0))
            slider.setToolTip(item.tooltip)

            value_label = QLabel(str(item.default))
            value_label.setMinimumWidth(36)
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)

            slider.valueChanged.connect(
                lambda v, lbl=value_label, k=item.key: (
                    lbl.setText(str(v)),
                    self.valueChanged.emit(k, v),
                )
            )

            hbox.addWidget(slider)
            hbox.addWidget(value_label)
            # Slider-Referenz merken, damit get_value/set_config darauf zugreifen können
            container.slider = slider  # type: ignore[attr-defined]
            return container

        elif item.kind == "int":
            w = QSpinBox()
            w.setMinimum(int(item.minimum))
            w.setMaximum(int(item.maximum))
            w.setSingleStep(int(item.step))
            w.setValue(int(item.default or 0))
            w.setToolTip(item.tooltip)
            w.valueChanged.connect(lambda v, k=item.key: self.valueChanged.emit(k, v))
            return w

        elif item.kind == "float":
            w = QDoubleSpinBox()
            w.setDecimals(item.decimals)
            w.setMinimum(item.minimum)
            w.setMaximum(item.maximum)
            w.setSingleStep(item.step)
            w.setValue(float(item.default or 0.0))
            w.setToolTip(item.tooltip)
            w.valueChanged.connect(lambda v, k=item.key: self.valueChanged.emit(k, v))
            return w

        elif item.kind == "text":
            w = QLineEdit(str(item.default) if item.default is not None else "")
            w.setToolTip(item.tooltip)
            w.textChanged.connect(lambda v, k=item.key: self.valueChanged.emit(k, v))
            return w

        raise ValueError(f"unkown PluginItem.kind: {item.kind!r}")

    # ------------------------------------------------------------------
    # access values
    # ------------------------------------------------------------------
    def is_active(self) -> bool:
        return self.isChecked()

    def get_value(self, key: str) -> Any:
        widget = self._widgets[key]
        item = self._items[key]
        if item.kind == "separator":
            return None
        if item.kind == "checkbox":
            return widget.isChecked()  # type: ignore[attr-defined]
        if item.kind == "slider":
            return widget.slider.value()  # type: ignore[attr-defined]
        if item.kind in ("int", "float"):
            return widget.value()  # type: ignore[attr-defined]
        if item.kind == "text":
            return widget.text()  # type: ignore[attr-defined]
        raise ValueError(item.kind)

    def get_config(self) -> dict[str, Any]:
        """Liest 'active' + alle Config-Werte in ein dict (z.B. für JSON-Speicherung)."""
        cfg: dict[str, Any] = {"active": self.is_active()}
        for key, item in self._items.items():
            if item.kind == "separator":
                continue
            cfg[key] = self.get_value(key)
        return cfg

    def set_config(self, cfg: dict[str, Any]) -> None:
        """Setzt 'active' + Config-Werte aus einem dict (z.B. beim Laden gespeicherter Settings)."""
        if "active" in cfg:
            self.setChecked(bool(cfg["active"]))
        for key, value in cfg.items():
            if key == "active" or key not in self._widgets:
                continue
            widget = self._widgets[key]
            item = self._items[key]
            if item.kind == "separator":
                continue
            elif item.kind == "checkbox":
                widget.setChecked(bool(value))  # type: ignore[attr-defined]
            elif item.kind == "slider":
                widget.slider.setValue(int(value))  # type: ignore[attr-defined]
            elif item.kind in ("int", "float"):
                widget.setValue(value)  # type: ignore[attr-defined]
            elif item.kind == "text":
                widget.setText(str(value))  # type: ignore[attr-defined]

class Plugin():
    """Abstract Base Class for Plugins."""

    def __init__(self, context: PluginContext):
        self.context = context

    def setUp(self, key: str, title: str, items: PluginItem, columns: int = 5):
        self.plugin_items = items
        self.key_name = key
        self.title = title
        self.columns = columns
        self._config = (self.context.config.get(self.key_name, {}) or {})
        self.context.siril.log(f"setup plugin: {self.title}", LogColor.GREEN)

    def create_plugin_box(self):
        """everything needed for the widget."""
        has_process = type(self).process is not Plugin.process
        has_load = type(self).load is not Plugin.load

        self.box = PluginConfigBox(self.title, self.plugin_items, active=self._config.get("active", True), show_process_button=has_process, show_load_button=has_load, columns=self.columns)

        if has_process:
            self.box.processRequested.connect(self._on_process)
        if has_load:
            self.box.loadRequested.connect(self._on_load)

        return self.box

    # Single siril command execution with logging
    def cmd(self, *args):
        self.context.siril.log(f"[CMD] {' '.join(args)}", LogColor.GREEN)
        self.context.siril.cmd(*args)

    def get_key_name(self):
        """returns the key name of the plugin."""
        return self.key_name

    def get_plugin_name(self):
        """returns the title of the plugin."""
        return self.title

    def _on_process(self):
        workdir = self.get_siril_wd()
        has_load = type(self).load is not Plugin.load
        try:
            self.process()
        except Exception as e:
            self.context.siril.log(f"Error during execution: {e}",LogColor.RED)
        self.cmd("cd",workdir)
        if has_load:
            self.load()       

    def _on_load(self):
        self.load()

    def process(self):
        """everything needed for the processing."""
        pass

    def load(self):
        """everything needed for the processing."""
        pass

    def seril(self):
        return self.context.siril

    def get_siril_wd(self):
        return self.context.siril.get_siril_wd()

    def get_value(self, key: str):
        return self.box.get_value(key)
    
    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value

    