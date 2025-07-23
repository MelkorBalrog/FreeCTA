from dataclasses import dataclass, field

@dataclass
class MissionProfile:
    name: str
    tau_on: float = 0.0
    tau_off: float = 0.0
    board_temp: float = 25.0
    board_temp_min: float = 25.0
    board_temp_max: float = 25.0
    ambient_temp: float = 25.0
    ambient_temp_min: float = 25.0
    ambient_temp_max: float = 25.0
    humidity: float = 50.0
    duty_cycle: float = 1.0
    notes: str = ""

    @property
    def temperature(self) -> float:
        """Alias for backward compatibility (returns board temperature)."""
        return self.board_temp

    @temperature.setter
    def temperature(self, value: float) -> None:
        self.board_temp = value


    @property
    def tau(self) -> float:
        """Return the total TAU for backward compatibility."""
        return self.tau_on + self.tau_off

@dataclass
class ReliabilityComponent:
    name: str
    comp_type: str
    quantity: int = 1
    attributes: dict = field(default_factory=dict)
    qualification: str = ""
    fit: float = 0.0
    is_passive: bool = False
    sub_boms: list = field(default_factory=list)

QUALIFICATIONS = [
    "AEC-Q100",
    "AEC-Q101",
    "AEC-Q200",
    "IECQ",
    "MIL-STD-883",
    "MIL-PRF-38534",
    "MIL-PRF-38535",
    "Space",
    "None",
]

@dataclass
class ReliabilityAnalysis:
    """Store the results of a reliability calculation including the BOM."""

    name: str
    standard: str
    profile: str
    components: list
    total_fit: float
    spfm: float
    lpfm: float
    dc: float

@dataclass
class HazopEntry:
    function: str
    malfunction: str
    mtype: str
    scenario: str
    conditions: str
    hazard: str
    safety: bool
    rationale: str
    covered: bool
    covered_by: str
    component: str = ""

@dataclass
class HaraEntry:
    malfunction: str
    severity: int
    sev_rationale: str
    controllability: int
    cont_rationale: str
    exposure: int
    exp_rationale: str
    asil: str
    safety_goal: str

@dataclass
class HazopDoc:
    """Container for a HAZOP with a name and list of entries."""
    name: str
    entries: list

@dataclass
class HaraDoc:
    """Container for a HARA linked to a specific HAZOP."""
    name: str
    hazop: str
    entries: list
    approved: bool = False

COMPONENT_ATTR_TEMPLATES = {
    "capacitor": {
        "dielectric": ["ceramic", "electrolytic", "tantalum"],
        "capacitance_uF": "",
        "voltage_V": "",
        "esr_ohm": "",
        "tolerance_pct": "",
    },
    "resistor": {
        "resistance_ohm": "",
        "power_W": "",
        "tolerance_pct": "",
    },
    "inductor": {
        "inductance_H": "",
        "current_A": "",
        "saturation_A": "",
    },
    "diode": {
        "type": ["standard", "zener", "schottky"],
        "reverse_V": "",
        "forward_current_A": "",
    },
    "transistor": {
        "transistor_type": ["BJT", "MOSFET"],
        "pins": "",
        "voltage_V": "",
        "current_A": "",
    },
    "ic": {
        "type": ["digital", "analog", "mcu"],
        "pins": "",
        "transistors": "",
    },
    "connector": {"pins": ""},
    "relay": {"cycles": "", "current_A": "", "voltage_V": ""},
    "switch": {"cycles": "", "current_A": "", "voltage_V": ""},
}

RELIABILITY_MODELS = {
    "IEC 62380": {
        "capacitor": {
            "text": "Base*(1+T/100)*Duty*(1+V/100)",
            "formula": lambda a, mp: (0.02 if a.get("dielectric", "ceramic") == "ceramic" else 0.04)
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + float(a.get("voltage_V", 0)) / 100.0)
            * mp.duty_cycle,
        },
        "resistor": {
            "text": "0.005*(1+T/100)*Duty*(1+P/10)",
            "formula": lambda a, mp: 0.005
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + float(a.get("power_W", 0)) / 10.0)
            * mp.duty_cycle,
        },
        "inductor": {
            "text": "0.004*(1+T/100)*Duty*(1+I/10)",
            "formula": lambda a, mp: 0.004
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + float(a.get("current_A", 0)) / 10.0)
            * mp.duty_cycle,
        },
        "diode": {
            "text": "0.008*(1+T/100)*Duty*(1+VR/100)",
            "formula": lambda a, mp: 0.008
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + float(a.get("reverse_V", 0)) / 100.0)
            * mp.duty_cycle,
        },
        "transistor": {
            "text": "Base*(1+T/100)*Duty*(1+I/10) (base=0.01 BJT, 0.012 MOSFET)",
            "formula": lambda a, mp: (0.01 if a.get("transistor_type", "BJT") == "BJT" else 0.012)
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + float(a.get("current_A", 0)) / 10.0)
            * mp.duty_cycle,
        },
        "ic": {
            "text": "Base*(1+T/100)*Duty*(1+pins/1000)*(1+trans/1e6) (base=0.04 analog, 0.03 digital, 0.05 MCU)",
            "formula": lambda a, mp: (0.04 if a.get("type", "digital") == "analog" else 0.05 if a.get("type") == "mcu" else 0.03)
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * mp.duty_cycle
            * (1 + float(a.get("pins", 0)) / 1000.0)
            * (1 + float(a.get("transistors", 0)) / 1_000_000.0),
        },
        "connector": {
            "text": "0.002*(1+T/100)*Duty*(1+pins/100)",
            "formula": lambda a, mp: 0.002
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + float(a.get("pins", 0)) / 100.0)
            * mp.duty_cycle,
        },
        "relay": {
            "text": "0.03*(1+T/100)*Duty*(cycles/1e6)*(1+I/10)",
            "formula": lambda a, mp: 0.03
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * mp.duty_cycle
            * (float(a.get("cycles", 1e6)) / 1e6)
            * (1 + float(a.get("current_A", 0)) / 10.0),
        },
        "switch": {
            "text": "0.02*(1+T/100)*Duty*(cycles/1e6)*(1+I/10)",
            "formula": lambda a, mp: 0.02
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * mp.duty_cycle
            * (float(a.get("cycles", 1e6)) / 1e6)
            * (1 + float(a.get("current_A", 0)) / 10.0),
        },
    },
    "SN 29500": {
        "capacitor": {
            "text": "0.03*(1+T/100)*Duty*(1+V/100)",
            "formula": lambda a, mp: 0.03
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + float(a.get("voltage_V", 0)) / 100.0)
            * mp.duty_cycle,
        },
        "resistor": {
            "text": "0.006*(1+T/100)*Duty*(1+P/10)",
            "formula": lambda a, mp: 0.006
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + float(a.get("power_W", 0)) / 10.0)
            * mp.duty_cycle,
        },
        "inductor": {
            "text": "0.005*(1+T/100)*Duty*(1+I/10)",
            "formula": lambda a, mp: 0.005
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + float(a.get("current_A", 0)) / 10.0)
            * mp.duty_cycle,
        },
        "diode": {
            "text": "0.009*(1+T/100)*Duty*(1+VR/100)",
            "formula": lambda a, mp: 0.009
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + float(a.get("reverse_V", 0)) / 100.0)
            * mp.duty_cycle,
        },
        "transistor": {
            "text": "Base*(1+T/100)*Duty*(1+I/10) (base=0.012 BJT, 0.014 MOSFET)",
            "formula": lambda a, mp: (0.012 if a.get("transistor_type", "BJT") == "BJT" else 0.014)
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + float(a.get("current_A", 0)) / 10.0)
            * mp.duty_cycle,
        },
        "ic": {
            "text": "Base*(1+T/100)*Duty*(1+pins/1000)*(1+trans/1e6) (base=0.05 analog, 0.04 digital, 0.06 MCU)",
            "formula": lambda a, mp: (0.05 if a.get("type", "digital") == "analog" else 0.06 if a.get("type") == "mcu" else 0.04)
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * mp.duty_cycle
            * (1 + float(a.get("pins", 0)) / 1000.0)
            * (1 + float(a.get("transistors", 0)) / 1_000_000.0),
        },
        "connector": {
            "text": "0.003*(1+T/100)*Duty*(1+pins/100)",
            "formula": lambda a, mp: 0.003
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + float(a.get("pins", 0)) / 100.0)
            * mp.duty_cycle,
        },
        "relay": {
            "text": "0.035*(1+T/100)*Duty*(cycles/1e6)*(1+I/10)",
            "formula": lambda a, mp: 0.035
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * mp.duty_cycle
            * (float(a.get("cycles", 1e6)) / 1e6)
            * (1 + float(a.get("current_A", 0)) / 10.0),
        },
        "switch": {
            "text": "0.025*(1+T/100)*Duty*(cycles/1e6)*(1+I/10)",
            "formula": lambda a, mp: 0.025
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * mp.duty_cycle
            * (float(a.get("cycles", 1e6)) / 1e6)
            * (1 + float(a.get("current_A", 0)) / 10.0),
        },
    },
}

global_requirements = {}
# ASIL level options including decomposition levels
ASIL_LEVEL_OPTIONS = [
    "QM", "QM(A)", "QM(B)", "QM(C)", "QM(D)",
    "A", "A(B)", "B", "B(C)", "C", "C(D)", "D"
]

ASIL_ORDER = {"QM":0, "A":1, "B":2, "C":3, "D":4}
ASIL_TARGETS = {
    "D": {"spfm":0.99, "lpfm":0.90, "dc":0.99},
    "C": {"spfm":0.97, "lpfm":0.90, "dc":0.97},
    "B": {"spfm":0.90, "lpfm":0.60, "dc":0.90},
    "A": {"spfm":0.0, "lpfm":0.0, "dc":0.0},
    "QM": {"spfm":0.0, "lpfm":0.0, "dc":0.0},
}

# Simplified ISO 26262 risk graph for ASIL determination
ASIL_TABLE = {
    (3, 1, 4): "D", (3, 1, 3): "D", (3, 1, 2): "C", (3, 1, 1): "B",
    (3, 2, 4): "C", (3, 2, 3): "C", (3, 2, 2): "B", (3, 2, 1): "A",
    (3, 3, 4): "B", (3, 3, 3): "B", (3, 3, 2): "A", (3, 3, 1): "QM",
    (2, 1, 4): "C", (2, 1, 3): "C", (2, 1, 2): "B", (2, 1, 1): "A",
    (2, 2, 4): "B", (2, 2, 3): "B", (2, 2, 2): "A", (2, 2, 1): "QM",
    (2, 3, 4): "A", (2, 3, 3): "A", (2, 3, 2): "QM", (2, 3, 1): "QM",
}

def calc_asil(sev: int, cont: int, expo: int) -> str:
    """Return ASIL based on severity, controllability and exposure."""
    return ASIL_TABLE.get((sev, cont, expo), "QM")
