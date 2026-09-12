import shutil
from pathlib import Path
from dataclasses import dataclass
from originM2lib.om2_plugin import Plugin, PluginContext, PluginItem
from sirilpy import LogColor

class CalibratePlugin(Plugin):

    result_name = "calibration"

    calibrate_items = [
        PluginItem(kind="checkbox",  key="cfa",          label="CFA format",   default=False),
        PluginItem(kind="checkbox",  key="equalize_cfa", label="equalize CFA", default=False),
        PluginItem(kind="checkbox",  key="debayer",      label="Debayer",      default=False),
        PluginItem(kind="separator", key="sep1"),
        PluginItem(kind="int",       key="sigma_low",    label="Sigma Low",    default=3),
        PluginItem(kind="int",       key="sigma_high",   label="Sigma High",   default=3),
    ]

    def __init__(self, context: PluginContext):
        super().__init__(context)
        self.setUp("calibrate", "Calibrate", self.calibrate_items)

    def process(self):
        # ── 1) Convert Lights ─────────────────────────────
        self.context.siril.log(f"[INFO] prepare light", LogColor.GREEN)
        self.cmd("cd","lights")
        self.cmd("convert","light","-out=../process")
        self.cmd("cd","../process")

        # ── 2) Calibrate the images ─────────────────────────────
        args = ["calibrate","light","-bias=../masters/bias_master","-dark=../masters/dark_master","-flat=../masters/flat_master"]
        if self.get_value("cfa"):
            args.append("-cfa ")
        if self.get_value("equalize_cfa"):
            args.append("-equalize_cfa")
        if self.get_value("debayer"):
            args.append("-debayer")
        self.context.siril.log(f"[INFO] calibrate", LogColor.GREEN)
        self.cmd(*args)        

        # ── 2) register ─────────────────────────────
        self.cmd("register","pp_light")
        # ── 3) stack the images ─────────────────────────────
        self.cmd("stack",
                 "r_pp_light",
                 "rej","3","3",
                 "-norm=addscale",
                 "-output_norm",
                 "-rgb_equal",
                 f"-out={self.result_name}"
                )

    def load(self):
        wd = self.get_siril_wd()
        self.cmd("load", f"{wd}/process/{self.result_name}")
