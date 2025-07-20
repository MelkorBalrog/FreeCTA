#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 Capek System Safety & Robotic Solutions
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
===============================================================================
Risk & Assurance Gate Calculator for Autonomous Systems
===============================================================================

Overview of the Provided Risk Assessment Approach
-------------------------------
This tool is a semi-quantitative method designed to assess the safety assurance 
of an autonomous system’s subsystems. It produces an Prototype Assurance Level (PAL) (on a scale 
from 1 to 5) using qualitative labels that describe the required level of safety 
measures. For example, the scale is defined as:

   1 → Extra Low  
   2 → Low  
   3 → Moderate  
   4 → High  
   5 → High+  

The goal is to identify potential safety gaps and determine the extra assurance 
(i.e. additional testing, validation, design modifications) needed before a 
prototype is approved for public road trials.

Inputs – Confidence, Robustness, and Direct Assurance Metrics
-------------------------------
Each subsystem is evaluated using three main inputs (each rated from 1 to 5):

  1. **Confidence Level (CL):** Reflects the quality and extent of testing/validation.
  2. **Robustness Score (RS):** Reflects the strength of design safeguards and redundancy.
     (Different criteria are applied for system functions versus human tasks.)
  3. **Direct Assurance:** Pre-assessed assurance values derived from safety analyses.

For basic (leaf) nodes the provided ratings are used directly.

Computation Logic and Manual Calculation
-------------------------------

### 1. Deriving an Prototype Assurance Level (PAL) from Base Inputs
When only Confidence and Robustness values are provided, the tool “inverts” these 
inputs to yield a base Prototype Assurance Level (PAL). In this method, low confidence and low robustness 
result in a high assurance requirement (i.e. “High+”), while high confidence and high robustness 
yield a low assurance requirement (i.e. “Extra Low”).

**Assurance Matrix for Base Inputs (Qualitative Labels)**

|                           | **Confidence: Extra Low** | **Confidence: Low**   | **Confidence: Moderate** | **Confidence: High** | **Confidence: High+** |
|---------------------------|---------------------------|-----------------------|--------------------------|----------------------|-----------------------|
| **Robustness: Extra Low** | High+                     | High+                 | High                     | High                 | High                  |
| **Robustness: Low**       | High+                     | High+                 | High                     | Moderate             | Moderate              |
| **Robustness: Moderate**  | High                      | High                  | Moderate                 | Moderate             | Extra Low             |
| **Robustness: High**      | High                      | Moderate              | Moderate                 | Extra Low            | Extra Low             |
| **Robustness: High+**     | High                      | Moderate              | Extra Low                | Extra Low            | Extra Low             |

*Interpretation:*  
– Very poor testing and design (i.e. both “Extra Low”) lead to a “High+” assurance requirement.  
– Excellent testing and design (i.e. both “High+”) result in an “Extra Low” requirement.  
– Mixed values yield intermediate Prototype Assurance Levels (PAL).

---

### 2. Aggregating Prototype Assurance Levels (PAL) from Child Nodes

When a parent node aggregates Prototype Assurance Levels (PAL) from its children, the aggregation method 
depends on the logical gate connecting them:

#### For an **AND Gate**:
All components must be robust, so the overall assurance is determined by combining the child 
levels using a reliability-inspired approach. Use the following qualitative guideline:

**Aggregation Table for AND Gate (Qualitative Labels)**

|                         | **Child 2: Extra Low** | **Child 2: Low**   | **Child 2: Moderate** | **Child 2: High**   | **Child 2: High+**  |
|-------------------------|------------------------|--------------------|-----------------------|---------------------|---------------------|
| **Child 1: Extra Low**  | Extra Low              | Extra Low          | Low                   | High                | High+               |
| **Child 1: Low**        | Extra Low              | Low                | Moderate              | High                | High+               |
| **Child 1: Moderate**   | Low                    | Moderate           | High                  | High+               | High+               |
| **Child 1: High**       | High                   | High               | High+                 | High+               | High+               |
| **Child 1: High+**      | High+                  | High+              | High+                 | High+               | High+               |

*Interpretation:*  
– Combining two “High+” components remains “High+.”  
– If one component is significantly lower, the overall requirement shifts toward a higher assurance need.

#### For an **OR Gate**:
When alternative options are available, a simple average (by converting the qualitative levels 
to an ordered scale) is used. A strong alternative (e.g. “High+”) can partially offset a weaker one 
(e.g. “Low”).

---

### 3. Decomposing a Parent Prototype Assurance Level (PAL) into Child Targets

A parent node’s overall assurance requirement can be decomposed into target Prototype Assurance Levels (PAL) 
for its children. The following guidelines serve as a reference for common decompositions:

**Decomposition Guidelines**

- **Parent Assurance: High+**  
  – Option A: Both children target “High.”  
  – Option B: One child may target “High+” while the other targets “Extra Low” so that their combined effect meets the “High+” requirement.
  
- **Parent Assurance: High**  
  – Children should typically target between “Moderate” and “High.”

- **Parent Assurance: Moderate**  
  – Children should have targets in the range of “Low” to “Moderate.”

- **Parent Assurance: Low**  
  – Children should target “Extra Low” or “Low.”

- **Parent Assurance: Extra Low**  
  – Both children should be “Extra Low.”

These rules ensure that when children’s Prototype Assurance Levels (PAL) are aggregated (using the AND or OR rules), 
they “reconstruct” the parent’s overall requirement.

---

### 4. Adjusting Assurance Based on Severity

Severity reflects the potential impact of a subsystem’s failure. It is used to adjust the computed 
Prototype Assurance Level (PAL) as follows:

- **General Rule (for most nodes):**  
  **Final Prototype Assurance Level (PAL) = (Aggregated Child Assurance + Highest Parent Severity) ÷ 2**  
  A higher severity (indicating more catastrophic consequences) increases the overall assurance requirement.

- **For Vehicle Level Functions:**  
  The node’s own severity is used instead of the parent’s. An example adjustment formula is:  
  **Adjusted Assurance = (2 × Computed Assurance) – (Node’s Own Severity)**  
  This modification increases the Prototype Assurance Level (PAL) when the potential impact is high.

---

### Discretization Tables
The following tables map raw numeric inputs to discrete levels that are then translated into qualitative labels:

1) **Confidence Level**

   +-------+------------------------+-----------------------------------------------+
   | Level | Description            | Expert Criteria                               |
   +-------+------------------------+-----------------------------------------------+
   |   1   | Very poor confidence   | No testing or validation evidence.           |
   |   2   | Poor confidence        | Minimal testing; incomplete evidence.        |
   |   3   | Moderate confidence    | Some validation; moderate evidence.          |
   |   4   | High confidence        | Well-tested with redundant checks.           |
   |   5   | Excellent confidence   | Comprehensive testing & strong evidence.     |
   +-------+------------------------+-----------------------------------------------+

2) **Robustness (Function)**

   +-------+--------------------------+---------------------------------------------+
   | Score | Description             | Rationale (Safety Loading)                  |
   +-------+--------------------------+---------------------------------------------+
   |   1   | Very Poor Safety Load   | Minimal redundancy; fails to mitigate risks.|
   |   2   | Poor Safety Load        | Only basic safety measures.                 |
   |   3   | Moderate Safety Load    | Standard protection; moderate redundancy.   |
   |   4   | High Safety Load        | Strong redundancy & mitigations.            |
   |   5   | Excellent Safety Load   | Full redundancy & comprehensive measures.   |
   +-------+--------------------------+---------------------------------------------+

3) **Robustness (Human Task)**

   +-------+--------------------------+----------------------------------------------+
   | Level | Description            | Expert Criteria for a Human Task             |
   +-------+--------------------------+----------------------------------------------+
   |   1   | Very poor performance  | Minimal training; slow reaction times.       |
   |   2   | Poor performance       | Limited training; suboptimal responses.      |
   |   3   | Moderate performance   | Adequately trained; acceptable reactions.    |
   |   4   | High performance       | Very experienced; quick & sound decisions.   |
   |   5   | Excellent performance  | Expert-level with flawless performance.      |
   +-------+--------------------------+----------------------------------------------+

---

### Summary of Qualitative Assurance Labels

- **Extra Low:** Minimal assurance required (system is very safe).
- **Low:** Some assurance is required.
- **Moderate:** A moderate level of additional assurance is needed.
- **High:** Significant additional assurance is required.
- **High+:** Maximum assurance is required (system is highly unsafe without improvements).

---

### Additional Notes on the Calculation Process

- **Combining Direct Inputs:**  
  If any direct assurance inputs are provided, they are combined using logical gate rules:
  
  - **OR Gate:** Inputs are averaged.
  - **AND Gate:** Inputs are combined using a “complement product” approach.

- **Adjustment with Severity:**  
  The final Prototype Assurance Level (PAL) is adjusted by incorporating the severity (using the highest parent severity unless the node is a Vehicle Level Function, in which case its own severity is used).

- **Decomposition and Aggregation:**  
  The parent node’s assurance requirement can be decomposed into target Prototype Assurance Levels (PAL) for its children (see Decomposition Guidelines above), and child Prototype Assurance Levels (PAL) are aggregated (using the AND/OR rules) to reconstruct the parent’s overall requirement.

-------------------------------
References
----------
- Rausand, M., & Høyland, A. (2004). *System Reliability Theory: Models, Statistical Methods, and Applications.* Wiley-Interscience.

===============================================================================
"""

import re
import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from review_toolbox import (
    ReviewToolbox,
    ReviewData,
    ReviewParticipant,
    ReviewComment,
    ParticipantDialog,
    ReviewScopeDialog,
    ReviewDocumentDialog,
    VersionCompareDialog,
)
from dataclasses import asdict
import json
import csv
import tkinter.font as tkFont
from PIL import Image, ImageDraw, ImageFont, ImageTk
import os
os.environ["GS_EXECUTABLE"] = r"C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe"
import networkx as nx
import matplotlib.pyplot as plt
# Import ReportLab for PDF export.
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, SimpleDocTemplate, Image as RLImage
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
import PIL.Image as PILImage
from reportlab.platypus import LongTable

styles = getSampleStyleSheet()  # Create the stylesheet.
preformatted_style = ParagraphStyle(name="Preformatted", fontName="Courier", fontSize=10)
styles.add(preformatted_style)

##########################################
# VALID_SUBTYPES dictionary
##########################################
VALID_SUBTYPES = {
    "Confidence": ["Function", "Human Task"],
    "Robustness": ["Function", "Human Task"],
    "Maturity": ["Functionality"],
    "Rigor": ["Capability", "Safety Mechanism"],
    "Prototype Assurance Level (PAL)": ["Vehicle Level Function"]
}

##########################################
# Global Unique ID Counter for Nodes
##########################################
unique_node_id_counter = 1
import math
import uuid

global_requirements = {}
# ASIL level options including decomposition levels
ASIL_LEVEL_OPTIONS = [
    "QM", "QM(A)", "QM(B)", "QM(C)", "QM(D)",
    "A", "A(B)", "B", "B(C)", "C", "C(D)", "D"
]
dynamic_recommendations = {
    1: {
        "Testing Requirements": (
            "Perform extensive scenario-based simulations covering normal driving, sensor failures, emergency braking, "
            "and boundary conditions. Conduct rigorous lab tests and closed-course trials to verify core ADS functions under ideal conditions. "
            "No public road tests are permitted until every core function is validated in a controlled prototype environment."
        ),
        "IFTD Responsibilities": (
            "A dedicated safety driver is in the vehicle at all times along with an engineer. The IFTD must be able to take immediate manual control "
            "when abnormal conditions are detected. Training focuses on achieving short reaction times and enhanced situational awareness through frequent emergency takeover drills."
        ),
        "Preventive Maintenance Actions": (
            "Conduct pre-trip and post-trip inspections on every run. Regularly calibrate, clean, and realign all sensors (cameras, radar, LiDAR). "
            "Maintain a detailed log and perform daily component checks to promptly address any anomalies before further testing."
        ),
        "Relevant AVSC Guidelines": (
            "Adhere to AVSC Best Practice for In-Vehicle clone Test Driver Selection, Training, and Oversight (AVSC00001-2019) and SAE J3018 guidelines, "
            "with extra emphasis on ensuring the IFTD can safely intervene in a prototype environment."
        ),
        "Extra Recommendations": {
            "steering": (
                "Include operational tests that simulate sudden, unintended steering inputs and verify that dynamic steering limiters are active. "
                "Ensure that the IFTD can promptly override any abnormal steering commands."
            ),
            "lateral": (
                "Design tests to simulate faulty lateral control (e.g., drifting or incorrect lane-keeping) and verify that any deviation is corrected within safe lateral boundaries. "
                "These tests shall include simulations, closed-course testing, and silent mode testing as required by the system’s rigor and child maturity."
            ),
            "longitudinal": (
                "Simulate sudden acceleration or deceleration events and verify that smooth speed transitions are maintained. "
                "Ensure that any unexpected longitudinal changes are managed safely by the IFTD."
            ),
            "braking": (
                "Simulate unintended or excessive braking events on a closed course and verify that the IFTD can quickly restore controlled braking and vehicle stability. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "deceleration": (
                "Develop test scenarios where deceleration is either too abrupt or delayed, and verify that the IFTD's intervention results in smooth, predictable slowdowns within defined limits."
            ),
            "acceleration": (
                "Test for unintended acceleration surges by simulating load changes and external disturbances. "
                "Verify that the IFTD can promptly override acceleration commands to maintain smooth, safe speed profiles."
            ),
            "park brake": (
                "Design controlled tests that trigger parking brake faults and verify that the system engages/disengages reliably. "
                "Ensure that the IFTD can safely manage the vehicle during such events."
            ),
            "parking brake": (
                "Conduct targeted tests simulating parking brake malfunctions, ensuring reliable engagement/disengagement and that the IFTD can intervene safely."
            ),
            "mode": (
                "Simulate mode indicator anomalies to verify that the IFTD receives clear, actionable alerts and can enforce proper system state transitions."
            ),
            "notification": (
                "Verify that the alert system responds accurately to simulated sensor or system errors in a controlled test environment. "
                "Ensure that alerts are displayed clearly via visual and auditory cues and are properly logged."
            ),
            "takeover": (
                "Simulate scenarios where the ADS disengages unexpectedly, requiring the IFTD to take over. "
                "Validate that the takeover mechanism enables the IFTD to quickly and safely assume manual control."
            ),
            "rollaway": (
                "Conduct basic simulation tests to verify that the system can detect a potential rollaway condition. "
                "Test the activation of emergency brakes and initial control protocols on a slight incline in a controlled laboratory environment."
            ),
            "control": (
                "Assess the IFTD’s basic manual override capability under simulated conditions. "
                "Ensure that, despite minimal training, the driver can momentarily assume control in a laboratory environment."
            )
        }
    },
    2: {
        "Testing Requirements": (
            "Initiate limited public-road tests under tightly controlled conditions (e.g., low-speed, daylight, good weather) within a constrained ODD. "
            "Employ advanced simulations—including fault injection, emergency braking, and scenario-based tests—alongside closed-course validations to verify safe operation."
        ),
        "IFTD Responsibilities": (
            "The safety driver (with a co-driver if necessary) continuously monitors the ADS and is ready to intervene immediately. "
            "Training drills focus on rapid manual intervention and maintaining situational awareness under varying test conditions."
        ),
        "Preventive Maintenance Actions": (
            "Implement both time-based and event-triggered inspections. Prior to each test, verify that sensor calibrations and system integrity meet safety standards. "
            "Document all findings comprehensively and address any anomalies immediately to support safe operation."
        ),
        "Relevant AVSC Guidelines": (
            "Follow AVSC Best Practice for Data Collection for ADS-DVs (AVSC00004-2020), comply with SAE J3018, and meet local regulatory standards, "
            "with a focus on enhancing IFTD control and training."
        ),
        "Extra Recommendations": {
            "steering": (
                "Design tests that simulate unexpected steering deviations and verify that the IFTD can safely override these inputs. "
                "These tests shall include simulations, closed-course testing, and silent mode testing as per the required rigor and maturity of child elements."
            ),
            "lateral": (
                "Simulate faulty lateral control scenarios to ensure that any drift or deviation is corrected by the IFTD within safe lateral boundaries. "
                "These tests shall include simulations, closed-course testing, and silent mode testing as required by the system’s rigor and maturity of child elements."
            ),
            "longitudinal": (
                "Incorporate scenarios that simulate sudden acceleration or deceleration events. "
                "Verify that the emergency override system responds to maintain safe speed profiles."
            ),
            "braking": (
                "Include tests that simulate unintended or excessive braking events and verify that the IFTD can quickly re-establish controlled braking. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "deceleration": (
                "Develop test scenarios to confirm that deceleration remains controlled, even if it is slightly delayed or abrupt. "
                "Verify that basic emergency intervention protocols are activated in a controlled environment."
            ),
            "acceleration": (
                "Test for unintended acceleration surges by simulating moderate load changes and external disturbances. "
                "Confirm that the emergency override system responds to maintain safe speed profiles."
            ),
            "park brake": (
                "Conduct controlled tests to simulate parking brake faults and verify that basic safety protocols, such as system alerts and initial brake engagement, function properly."
            ),
            "parking brake": (
                "Conduct controlled tests to simulate parking brake malfunctions and ensure that the system engages protective measures reliably."
            ),
            "mode": (
                "Simulate mode indicator anomalies to verify that the IFTD receives clear alerts and can trigger preliminary system checks."
            ),
            "notification": (
                "Test the alert system under controlled conditions to verify prompt and clear notification of sensor or system errors."
            ),
            "takeover": (
                "Simulate scenarios where the ADS unexpectedly disengages to ensure that the IFTD can assume manual control quickly."
            ),
            "rollaway": (
                "Perform controlled closed-course tests simulating a rollaway event on a mild slope. "
                "Validate that the emergency braking system engages, the transmission shifts to neutral, and that driver alerts are issued promptly."
            ),
            "control": (
                "Verify that the IFTD can take control during simple, low-speed scenarios. "
                "Ensure that the manual override interface provides clear signals for intervention under these controlled conditions."
            )
        }
    },
    3: {
        "Testing Requirements": (
            "Expand testing into a broader ODD using high-fidelity simulations and extended on-road trials. "
            "Include scenarios such as higher speeds, nighttime driving, and light rain, along with targeted fault-injection tests that challenge the ADS and verify that the IFTD can promptly intervene."
        ),
        "IFTD Responsibilities": (
            "The safety driver remains onboard as a continuous clone while the ADS handles most of the route. "
            "Enhanced training emphasizes rapid manual takeover and precise interpretation of ADS signals, reinforced by regular simulator and on-track drills."
        ),
        "Preventive Maintenance Actions": (
            "Establish a formal maintenance schedule combining regular and event-based inspections supported by on-board diagnostics and predictive analytics. "
            "Preemptively address any component degradation to ensure that the IFTD’s ability to intervene is never compromised."
        ),
        "Relevant AVSC Guidelines": (
            "Utilize AVSC Best Practice for Metrics and Methods for Assessing Safety Performance and continuous monitoring principles. "
            "Ensure periodic IFTD re-training and adhere to ISO 26262/21448 for functional safety."
        ),
        "Extra Recommendations": {
            "steering": (
                "Simulate abnormal steering responses and verify that the IFTD can override these inputs safely. "
                "These tests shall include simulations, closed-course testing, and silent mode testing as per the required rigor and the maturity of child elements."
            ),
            "lateral": (
                "Develop test scenarios that replicate lateral control failures and verify that the IFTD restores proper lateral stability within defined limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing as required by the system’s rigor and child maturity."
            ),
            "longitudinal": (
                "Design tests that simulate abrupt changes in speed and verify that manual override maintains smooth acceleration and deceleration within preset control limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing as required."
            ),
            "braking": (
                "Include tests for inconsistent braking responses and evaluate how quickly and effectively the IFTD can re-establish controlled braking within safe limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "deceleration": (
                "Test deceleration behavior under fault conditions, ensuring that even with anomalies the deceleration remains predictable and controllable. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "acceleration": (
                "Include scenarios that trigger unexpected acceleration surges and verify that the IFTD can promptly intervene to restore safe speed levels. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "park brake": (
                "Design tests that simulate parking brake faults and assess the IFTD's ability to safely manage the vehicle until normal operation is restored. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "parking brake": (
                "Design tests that simulate parking brake faults and assess the IFTD's ability to safely manage the vehicle until normal operation is restored. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "mode": (
                "Simulate mode indicator errors and confirm that the IFTD is alerted to enforce correct system state transitions. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "notification": (
                "During extended on-road trials, verify that the notification system integrates with live sensor data to produce real alerts. "
                "Ensure that alerts are clearly presented—via both visual and auditory channels—and that the IFTD can respond promptly under dynamic conditions. "
                "Also, conduct performance studies to assess the IFTD's alert perception, reaction time, and controllability."
            ),
            "takeover": (
                "Develop complex scenarios that require the IFTD to take over from the ADS during fault conditions. "
                "Monitor response time and the system’s ability to safely transition to manual control, and conduct detailed post-event analyses."
            ),
            "rollaway": (
                "Simulate a truck rollaway scenario on a declining grade under controlled conditions. "
                "Verify that the vehicle's emergency braking, transmission neutralization, and electronic stability controls engage promptly to prevent uncontrolled movement. "
                "Ensure that tests include driver override procedures and proper system logging for subsequent analysis."
            ),
            "control": (
                "Confirm that the IFTD consistently demonstrates the ability to assume control during operational tests. "
                "The manual override interface should be intuitive, providing timely feedback and clear signals to the driver."
            )
        }
    },
    4: {
        "Testing Requirements": (
            "Conduct pilot tests in a quasi-commercial setting on intended routes under realistic conditions. "
            "Test the ADS across its full ODD—including boundary scenarios—using advanced simulations and on-road trials designed to safely challenge system limits."
        ),
        "IFTD Responsibilities": (
            "An IFTD is onboard at all times as the ultimate safety net. Although interventions become less frequent, the driver must remain vigilant and undergo regular drills "
            "and attention tests to ensure sustained manual control readiness under operational conditions."
        ),
        "Preventive Maintenance Actions": (
            "Integrate comprehensive preventive maintenance into the test cycle. Perform extensive pre-run system checks (HD map verification, sensor cleaning, redundant system tests) "
            "to confirm that all components operate reliably, thereby supporting uninterrupted IFTD oversight."
        ),
        "Relevant AVSC Guidelines": (
            "Implement AVSC Best Practice for First Responder Interactions and adopt a standardized Safety Inspection Framework. "
            "Ensure continuous monitoring and compliance with regulatory requirements (e.g., FMCSA, state DOT), with extra emphasis on IFTD training and rapid intervention procedures."
        ),
        "Extra Recommendations": {
            "steering": (
                "Include operational tests verifying that unexpected steering deviations are safely managed by the IFTD, with control limits enforced. "
                "These tests shall include simulations, closed-course testing, and silent mode testing as required."
            ),
            "lateral": (
                "Simulate faulty lateral control scenarios and verify that any drift or deviation is corrected by the IFTD within safe lateral boundaries. "
                "These tests shall include simulations, closed-course testing, and silent mode testing as required by the system’s rigor and maturity of child elements."
            ),
            "longitudinal": (
                "Design tests that simulate abrupt or erratic longitudinal events. Verify that manual override smoothly restores safe acceleration and deceleration within predefined control limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "braking": (
                "Conduct tests simulating unintended or excessive braking events and verify that the IFTD can rapidly re-establish controlled braking with predictable deceleration. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "deceleration": (
                "Include scenarios that ensure deceleration remains smooth and within safe limits even under abnormal conditions, with timely IFTD intervention if needed. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "acceleration": (
                "Test for unexpected acceleration surges and verify that the IFTD can safely override to restore smooth acceleration within acceptable limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "park brake": (
                "Perform targeted tests on parking brake engagement under fault conditions to verify reliable operation and that the IFTD can safely manage the vehicle within defined control limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "parking brake": (
                "Perform targeted tests on parking brake engagement under fault conditions to verify reliable operation and that the IFTD can safely manage the vehicle within defined control limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "mode": (
                "Simulate mode indicator anomalies and verify that the IFTD receives clear, actionable alerts to enforce correct system state transitions, "
                "while ensuring control limits are maintained. These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "notification": (
                "During pilot operations, validate that the notification system generates real-time alerts in response to actual sensor malfunctions or system deviations. "
                "Ensure that alerts are unambiguous and use multiple modalities (visual and auditory) to prompt immediate manual intervention if required. "
                "Additionally, perform targeted studies to measure the IFTD's alert perception, reaction time, and controllability, and apply these insights to refine both the alert mechanisms and driver training protocols."
            ),
            "takeover": (
                "Conduct pilot tests that incorporate controlled takeover scenarios. Assess the responsiveness, accuracy, and smoothness of manual intervention when the ADS disengages. "
                "Measure key performance metrics such as takeover speed and transition stability, and use these data to further refine both the takeover mechanism and IFTD training protocols."
            ),
            "rollaway": (
                "Under more demanding conditions, simulate a truck rollaway on a steeper decline with higher speeds. "
                "Verify that advanced emergency protocols—including enhanced trailer locking mechanisms and improved driver alert systems—are activated. "
                "Ensure that the vehicle's redundant braking and stability control systems work in tandem, and that the system facilitates timely driver override if required."
            ),
            "control": (
                "Ensure that the IFTD reliably assumes control in complex scenarios. "
                "The system should deliver clear override signals, and the driver must demonstrate enhanced situational awareness and rapid response under challenging conditions."
            )
        }
    },
    5: {
        "Testing Requirements": (
            "Subject the ADS to rigorous edge-case validations and continuous simulation exercises that safely challenge the system across its entire ODD. "
            "Design test scenarios to deliberately trigger abnormal conditions so that control limits are enforced and the IFTD remains fully prepared to intervene."
        ),
        "IFTD Responsibilities": (
            "Even at the highest automation level, an IFTD is always onboard as a failsafe. Their role is primarily supervisory, yet they undergo continuous, intensive training "
            "and periodic drills—including attention-enhancing measures such as periodic system alerts—to ensure immediate manual control if any sensor or system fault occurs."
        ),
        "Preventive Maintenance Actions": (
            "Maintain standard commercial fleet maintenance protocols with automated self-checks and condition-based preventive measures. "
            "Conduct frequent system health verifications—including sensor recalibration, hardware diagnostics, and software integrity tests—to ensure that control limits are consistently maintained and the IFTD oversight remains uncompromised."
        ),
        "Relevant AVSC Guidelines": (
            "Implement all applicable AVSC best practices—including continuous monitoring, first responder protocols, and transparency standards. "
            "Adhere to industry certifications (e.g., ANSI/UL 4600, ISO 26262/21448) while emphasizing rigorous IFTD training, enhanced system controllability, and rapid manual intervention within defined control limits."
        ),
        "Extra Recommendations": {
            "steering": (
                "Include operational tests verifying that dynamic steering limiters are active and that the IFTD can safely intervene when steering inputs exceed defined control limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing as required."
            ),
            "lateral": (
                "Design tests to simulate faulty lateral control and verify that any drift or deviation is corrected by the IFTD within safe lateral boundaries. "
                "These tests shall include simulations, closed-course testing, and silent mode testing as required by the system’s rigor and the maturity of all child elements."
            ),
            "longitudinal": (
                "Develop scenarios that test the smooth manual override of acceleration and deceleration controls, ensuring that any unexpected longitudinal changes are managed within preset control limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing as required."
            ),
            "braking": (
                "Include test cases for unintended or excessive braking, confirming that the IFTD can immediately assume control to restore safe braking within defined limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "deceleration": (
                "Verify through operational tests that deceleration remains smooth and controlled even when system signals are abnormal, ensuring timely IFTD intervention within safe deceleration limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "acceleration": (
                "Include scenarios to detect and safely manage any unintended acceleration surges, ensuring the IFTD can quickly override to maintain smooth speed transitions within acceptable limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "park brake": (
                "Perform targeted tests on parking brake engagement under fault conditions to ensure reliable performance and that the IFTD can safely manage the vehicle within defined control limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "parking brake": (
                "Perform targeted tests on parking brake engagement under fault conditions to ensure reliable performance and that the IFTD can safely manage the vehicle within defined control limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "mode": (
                "Simulate mode indicator anomalies and verify that the IFTD receives clear, actionable alerts to enforce correct system state transitions while maintaining operational control limits. "
                "These tests shall include simulations, closed-course testing, and silent mode testing."
            ),
            "notification": (
                "Under near-commercial conditions, monitor the notification alert system over extended periods to ensure that alerts are consistently delivered in real-time. "
                "Validate that alerts are unambiguous and use multiple modalities (visual and auditory) to prompt immediate manual intervention if required. "
                "Furthermore, conduct comprehensive studies to quantify the IFTD’s alert perception time, reaction time, and controllability, and apply these insights to refine both the alert mechanisms and driver training programs."
            ),
            "takeover": (
                "Even in near-commercial conditions, periodically simulate takeover events to ensure that the ADS remains fail-safe and that the IFTD can effectively intervene if required. "
                "Measure key performance metrics—such as takeover speed, accuracy, and smoothness of transition—and use these data to continuously refine the takeover mechanisms and improve IFTD training."
            ),
            "rollaway": (
                "Conduct exhaustive tests under worst-case rollaway scenarios, such as extended, steep grades combined with sensor or system faults. "
                "Ensure that all redundant systems, including emergency braking, transmission neutralization, and electronic stability controls, engage seamlessly. "
                "Validate the effectiveness of automated driver override protocols and comprehensive system logging to support post-incident analysis."
            ),
            "control": (
                "Validate that the IFTD can seamlessly assume complete control even under worst-case conditions. "
                "Extensive driver training, robust override interfaces, and redundant manual control mechanisms must be confirmed during rigorous testing."
            )
        }
    }
}

# Derived Maturity Table: (avg_confidence, avg_robustness) → maturity level
DERIVED_MATURITY_TABLE = {
    (1, 1): 1, (1, 2): 1, (1, 3): 1, (1, 4): 2, (1, 5): 2,
    (2, 2): 2, (2, 3): 2, (2, 4): 3, (2, 5): 3,
    (3, 3): 3, (3, 4): 3, (3, 5): 4,
    (4, 4): 4, (4, 5): 4,
    (5, 5): 5,
}

ASSURANCE_AGGREGATION_AND = {
    (1,1): 3,
    (1,2): 4, (2,2): 4,
    (1,3): 4, (2,3): 4, (3,3): 5,
    (1,4): 5, (2,4): 5, (3,4): 5, (4,4): 5,
    (1,5): 5, (2,5): 5, (3,5): 5, (4,5): 5, (5,5): 5
}

AND_DECOMPOSITION_TABLE = {
    3: [(1, 1)],
    4: [(1, 2), (2, 2), (1, 3), (2, 3)],
    5: [(1, 4), (2, 4), (3, 4), (4, 4),
        (1, 5), (2, 5), (3, 5), (4, 5), (5, 5)]
}

OR_DECOMPOSITION_TABLE = {
    1: [(5, 5)],
    2: [(4, 4)],
    3: [(3, 3)],
    4: [(2, 2)],
    5: [(1, 1)]
}
    
def boolify(value, default):
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value) if value is not None else default
        
class ADRiskAssessmentHelper:
    """
    Helper class for risk assessment computations.
    It encapsulates methods to:
      - Generate unique node IDs.
      - Update the unique ID counter based on a list of top events.
      - Round a value to the nearest half.
      - Discretize a continuous value into a level from 1 to 5.
      - Combine input values based on gate type.
      - Recursively calculate assurance (or maturity/rigor) values.
    """
    def __init__(self):
        self.unique_node_id_counter = 1

    def aggregate_clone_requirements(self, clone_node):
        """
        If the given node is a clone, then:
          - For each child in the original node, collect its safety requirements.
          - Gather safety goals from the clone's own parents and the original node's parents.
          - Link (i.e. add) these safety goals to each of the collected requirements.
        
        Returns a dictionary keyed by requirement key (its "id" if available, else its text)
        with each value containing:
             "req": the requirement dictionary,
             "linked_sgs": a set of safety goal strings.
        """
        # Only process if node is a clone
        if not clone_node.is_primary_instance and hasattr(clone_node, "original") and clone_node.original:
            aggregated = {}

            # 1. Collect requirements from each child of the original node.
            # (Assume that the safety requirements live on the base events.)
            children_reqs = []
            for child in clone_node.original.children:
                # You might want to further traverse children if needed; here we assume direct children.
                if hasattr(child, "safety_requirements") and child.safety_requirements:
                    children_reqs.extend(child.safety_requirements)
                else:
                    # Optionally, if child has its own children, traverse downward.
                    def collect_reqs(n):
                        reqs = []
                        if hasattr(n, "safety_requirements") and n.safety_requirements:
                            reqs.extend(n.safety_requirements)
                        for c in n.children:
                            reqs.extend(collect_reqs(c))
                        return reqs
                    children_reqs.extend(collect_reqs(child))
            
            # 2. Gather safety goals from the clone's immediate parents.
            clone_parent_goals = set()
            for parent in clone_node.parents:
                if parent.safety_goal_description and parent.safety_goal_description.strip():
                    clone_parent_goals.add(f"- {parent.safety_goal_description.strip()}")
                else:
                    clone_parent_goals.add(f"- {parent.name}")
            
            # 3. Also gather safety goals from the original node's immediate parents.
            original_parent_goals = set()
            for parent in clone_node.original.parents:
                if parent.safety_goal_description and parent.safety_goal_description.strip():
                    original_parent_goals.add(f"- {parent.safety_goal_description.strip()}")
                else:
                    original_parent_goals.add(f"- {parent.name}")
            
            # Union both sets.
            safety_goals = clone_parent_goals.union(original_parent_goals)
            print(f"DEBUG: For clone node {clone_node.unique_id}, clone_parent_goals={clone_parent_goals}, original_parent_goals={original_parent_goals}")

            # 4. For each collected requirement, add the safety goals.
            for req in children_reqs:
                key = req.get("id") if req.get("id") else req.get("text", "Unnamed Requirement")
                if key not in aggregated:
                    aggregated[key] = {
                        "req": req,
                        "linked_sgs": set()
                    }
                aggregated[key]["linked_sgs"].update(safety_goals)
                print(f"DEBUG: Linking safety goals {safety_goals} to requirement {key} from original child")
            return aggregated
        else:
            # If not a clone, return an empty dict (or handle as needed)
            return {}

    def fix_clone_references(self, root_nodes):
        # First pass: collect all primary nodes from every top event.
        primary_by_id = {}
        def collect_primary(node):
            if node.is_primary_instance:
                primary_by_id[node.unique_id] = node
                print(f"[DEBUG] Added primary node: id={node.unique_id}, name='{node.user_name}'")
            for child in node.children:
                collect_primary(child)
        for root in root_nodes:
            collect_primary(root)
        
        # Second pass: update all clones using the complete dictionary.
        def fix(node):
            if not node.is_primary_instance:
                orig_id = getattr(node, "_original_id", node.unique_id)
                print(f"[DEBUG] Fixing clone: id={node.unique_id}, _original_id={orig_id}")
                if orig_id in primary_by_id:
                    node.original = primary_by_id[orig_id]
                    print(f"[DEBUG] Clone {node.unique_id} now references primary node {node.original.unique_id}")
                else:
                    node.original = node
                    print(f"[DEBUG] No matching primary for clone {node.unique_id} with _original_id={orig_id}; using self")
            else:
                node.original = node
                print(f"[DEBUG] Primary node {node.unique_id} set to reference itself")
            for child in node.children:
                fix(child)
        for root in root_nodes:
            fix(root)

    def get_next_unique_id(self):
        uid = self.unique_node_id_counter
        self.unique_node_id_counter += 1
        return uid

    def update_unique_id_counter_for_top_events(self, top_events):
        def traverse(node):
            ids = [node.unique_id]
            for child in node.children:
                ids.extend(traverse(child))
            return ids
        all_ids = []
        for event in top_events:
            all_ids.extend(traverse(event))
        self.unique_node_id_counter = max(all_ids) + 1

    def round_to_half(self, val):
        try:
            val = float(val)
        except Exception as e:
            print(f"Error converting {val} to float: {e}")
            val = 0.0
        return round(val * 2) / 2

    def discretize_level(self, val):
        #r = self.round_to_half(val)
        r = val
        if r < 1.5:
            return 1
        elif r < 2.5:
            return 2
        elif r < 3.5:
            return 3
        elif r < 4.5:
            return 4
        else:
            return 5

    def combine_values(self, values, gate_type):
        if not values:
            return 1.0
        if gate_type.upper() == "AND":
            prod = 1.0
            for v in values:
                prod *= (1 - v/5)
            return (1 - prod) * 5
        else:
            return sum(values) / len(values)

    def combine_rigor_or(self,values):
        # Using the reliability (complement-product) formula.
        prod = 1.0
        for v in values:
            prod *= (1 - v/5)
        return round((1 - prod) * 5, 2)
        
    def combine_rigor_and(self,values):
        return sum(values) / len(values)            
            
    def combine_generic_values(self, values, gate_type):
        if not values:
            return None
        gate_type = gate_type.upper()
        if gate_type == "AND":
            prod = 1.0
            for v in values:
                prod *= (1 - round(v/5, 2))
            return round((1 - prod) * 5, 2)
        else:
            return round(sum(values) / len(values), 2)

    def is_effectively_confidence(self,node):
        """
        Returns True if the node is either:
          - A base event with node_type "CONFIDENCE LEVEL", or
          - A gate (or similar) whose children are all effectively confidence.
        """
        if node.node_type.upper() == "CONFIDENCE LEVEL":
            return True
        if node.children and node.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
            return all(self.is_effectively_confidence(child) for child in node.children)
        return False

    def is_effectively_robustness(self,node):
        """
        Returns True if the node is either:
          - A base event with node_type "ROBUSTNESS SCORE", or
          - A gate (or similar) whose children are all effectively robustness.
        """
        if node.node_type.upper() == "ROBUSTNESS SCORE":
            return True
        if node.children and node.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
            return all(self.is_effectively_robustness(child) for child in node.children)
        return False

    def aggregate_assurance_and(self,child_levels):
        """
        Combine a list of children’s Prototype Assurance Levels (PAL) for an AND gate,
        using pairwise lookups in ASSURANCE_AGGREGATION_AND.
        """
        if not child_levels:
            return 1
        current = child_levels[0]
        for next_val in child_levels[1:]:
            pair = tuple(sorted((current, next_val)))
            # If not found in the dict, fallback to max(...) or something:
            current = ASSURANCE_AGGREGATION_AND.get(pair, max(pair))
        return current

    def aggregate_assurance_or(self,child_levels):
        if not child_levels:
            return 1
        avg = sum(child_levels) // len(child_levels)
        return max(1, min(5, avg))

    def derive_assurance_from_base(self,conf_values, rob_values):
        """
        Given lists of confidence and robustness integers (each 1..5),
        compute a single 'inverted' Prototype Assurance Level (PAL) from 1..5,
        where low confidence/robustness inputs produce a high assurance value.
        """
        if not conf_values or not rob_values:
            return 1  # fallback
        # Compute the integer average for each
        avg_conf = round(sum(conf_values) / len(conf_values))
        avg_rob  = round(sum(rob_values) / len(rob_values))
        # Hard-coded 5×5 assurance matrix:
        assurance_matrix = [
          [5, 4, 4, 3, 3],  # Confidence = 1
          [4, 4, 3, 3, 2],  # Confidence = 2
          [4, 3, 3, 2, 2],  # Confidence = 3
          [3, 3, 2, 2, 1],  # Confidence = 4
          [3, 2, 2, 1, 1]   # Confidence = 5
        ]
        # Adjust indices (1 maps to index 0, etc.)
        c_idx = max(1, min(5, avg_conf)) - 1
        r_idx = max(1, min(5, avg_rob)) - 1
        return assurance_matrix[c_idx][r_idx]

    def get_highest_parent_severity_for_node(self, node, all_top_events):
        """
        Return the highest severity found among all ancestors of all instances
        (primary or clone) of 'node' across every top event in 'all_top_events'.
        If no ancestor has a valid severity, return 5 by default.
        """
        # 1) Identify the primary ID for the node
        primary_id = node.unique_id if node.is_primary_instance else node.original.unique_id

        # 2) Collect all instances (primary or clones) with that primary ID from all top events.
        instances = []
        def collect_instances(root):
            def walk(n):
                if n.is_primary_instance and n.unique_id == primary_id:
                    instances.append(n)
                elif (not n.is_primary_instance and n.original and 
                      n.original.unique_id == primary_id):
                    instances.append(n)
                for c in n.children:
                    walk(c)
            walk(root)
        for te in all_top_events:
            collect_instances(te)

        # 3) Traverse upward (using DFS) from each instance to find the maximum severity.
        visited = set()
        max_sev = 0
        def dfs_up(n):
            nonlocal max_sev
            if n in visited:
                return
            visited.add(n)
            if n.severity is not None:
                try:
                    s = int(n.severity)
                    if s > max_sev:
                        max_sev = s
                except:
                    pass
            for p in n.parents:
                dfs_up(p)
            # For clones, also check the original's parents.
            if (not n.is_primary_instance) and n.original and (n.original != n):
                for p2 in n.original.parents:
                    dfs_up(p2)
        for inst in instances:
            dfs_up(inst)
        return max_sev if max_sev > 0 else 5

    def aggregate_assurance_or_adjusted(self, child_levels):
        """
        For an OR gate, compute the average of the child levels and then invert the result using a 6 - average rule.
        For example, if the average child level is 4 (strong), then 6 - 4 = 2, meaning the overall assurance requirement is 2.
        Ensure the final value is between 1 and 5.
        """
        if not child_levels:
            return 1
        avg = sum(child_levels) / len(child_levels)
        inverted = 6 - avg
        return max(1, min(5, round(inverted)))

    def calculate_assurance_recursive(self, node, all_top_events, visited=None):
        if visited is None:
            visited = set()
        if node.unique_id in visited:
            return node.quant_value if node.quant_value is not None else 1
        visited.add(node.unique_id)
        t = node.node_type.upper()

        # --- Base Events ---
        if t == "CONFIDENCE LEVEL":
            cval = max(1, min(5, int(node.quant_value if node.quant_value is not None else 1)))
            node.quant_value = cval
            node.display_label = f"Confidence [{cval}]"
            node.detailed_equation = f"Base Confidence => {cval}"
            return cval
        if t == "ROBUSTNESS SCORE":
            rval = max(1, min(5, int(node.quant_value if node.quant_value is not None else 1)))
            node.quant_value = rval
            node.display_label = f"Robustness [{rval}]"
            node.detailed_equation = f"Base Robustness => {rval}"
            return rval

        if not node.children:
            fallback = max(1, min(5, int(node.quant_value if node.quant_value is not None else 1)))
            node.quant_value = fallback
            node.display_label = f"Node [{fallback}]"
            node.detailed_equation = f"No children => fallback value {fallback}"
            return fallback

        # Process all children recursively.
        for child in node.children:
            self.calculate_assurance_recursive(child, all_top_events, visited)

        # --- Separate children into base events and composite children ---
        base_values = []
        composite_values = []
        for child in node.children:
            ctype = child.node_type.upper()
            if ctype in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
                # Use the already computed quant_value (which is now the assurance value)
                base_values.append(max(1, min(5, int(child.quant_value))))
            else:
                composite_values.append(max(1, min(5, int(child.quant_value))))

        # For the base events, if present, compute the assurance using our inversion matrix.
        if base_values:
            # When only one type is present, we use the same list for both inputs.
            base_assurance = self.derive_assurance_from_base(base_values, base_values)
        else:
            base_assurance = None

        # For composite children, aggregate their assurance values using the appropriate gate rule.
        gate = (node.gate_type or "AND").upper()
        if composite_values:
            if gate == "AND":
                composite_assurance = self.aggregate_assurance_and(composite_values)
            elif gate == "OR":
                composite_assurance = self.aggregate_assurance_or_adjusted(composite_values)
            else:
                composite_assurance = None
        else:
            composite_assurance = None

        # Combine base assurance and composite assurance.
        if base_assurance is not None and composite_assurance is not None:
            combined = (base_assurance + composite_assurance) // 2
        elif base_assurance is not None:
            combined = base_assurance
        elif composite_assurance is not None:
            combined = composite_assurance
        else:
            combined = 1

        level_map = {1: "extra low", 2: "low", 3: "moderate", 4: "high", 5: "high+"}

        if node.node_type.upper() == "TOP EVENT":
            try:
                s = int(node.severity)
            except (TypeError, ValueError):
                s = 3
            s = max(1, min(5, s))
            
            try:
                c = int(node.controllability)
            except (TypeError, ValueError):
                c = 3
            c = max(1, min(5, c))

            final = round((combined + s + c) / 3)
            final = max(1, min(5, final))
            node.quant_value = final
            node.display_label = f"Prototype Assurance Level (PAL) [{level_map[final]}]"
            node.detailed_equation = (
                f"Base Assurance from children = {base_assurance if base_assurance is not None else 'N/A'}\n"
                f"Composite Assurance from gates = {composite_assurance if composite_assurance is not None else 'N/A'}\n"
                f"Combined (average) = {combined}\n"
                f"Node Severity (TOP EVENT) = {s}\n"
                f"Node Controllability = {c}\n"
                f"Final Assurance = (({combined} + {s} + {c}) /3) = {final}"
            )
            return final
        else:
            node.quant_value = combined
            node.display_label = f"Prototype Assurance Level (PAL) [{level_map[combined]}]"
            node.detailed_equation = (
                f"Base Assurance from children = {base_assurance if base_assurance is not None else 'N/A'}\n"
                f"Composite Assurance from gates = {composite_assurance if composite_assurance is not None else 'N/A'}\n"
                f"Combined Children Assurance (average) = {combined}\n"
            )
            return combined

    def calculate_probability_recursive(self, node, visited=None):
        """Recursively propagate failure probabilities using classical FTA rules."""
        if visited is None:
            visited = set()

        # Avoid infinite recursion but allow the same node to be evaluated
        # along different branches when it appears more than once.
        if node.unique_id in visited:
            return node.probability if node.probability is not None else 0.0

        visited.add(node.unique_id)
        t = node.node_type.upper()
        if t == "BASIC EVENT":
            prob = float(node.failure_prob)
            node.probability = prob
            node.display_label = f"P={prob:.2e}"
            return prob

        if not node.children:
            prob = float(getattr(node, "failure_prob", 0.0))
            node.probability = prob
            node.display_label = f"P={prob:.2e}"
            return prob

        # Use a fresh visited set for each child to ensure probabilities
        # propagate correctly even when subtrees are shared between gates.
        child_probs = [self.calculate_probability_recursive(c, visited.copy()) for c in node.children]

        gate = (node.gate_type or "AND").upper()
        if gate == "AND":
            prob = 1.0
            for p in child_probs:
                prob *= p
        else:
            prod = 1.0
            for p in child_probs:
                prod *= (1 - p)
            prob = 1 - prod
        node.probability = prob
        node.display_label = f"P={prob:.2e}"
        return prob


class FTADrawingHelper:
    """
    A helper class that provides drawing functions for fault tree diagrams.
    These methods can be used to draw shapes (gates, events, connectors, etc.)
    onto a tkinter Canvas.
    """
    def __init__(self):
        pass

    def get_text_size(self, text, font_obj):
        """Return the (width, height) in pixels needed to render the text with the given font."""
        lines = text.split("\n")
        max_width = max(font_obj.measure(line) for line in lines)
        height = font_obj.metrics("linespace") * len(lines)
        return max_width, height

    def draw_page_clone_shape(self, canvas, x, y, scale=40.0,
                              top_text="Desc:\n\nRationale:", bottom_text="Node",
                              fill="lightgray", outline_color="dimgray",
                              line_width=1, font_obj=None):
        # First, draw the main triangle using the existing triangle routine.
        self.draw_triangle_shape(canvas, x, y, scale=scale,
                                 top_text=top_text, bottom_text=bottom_text,
                                 fill=fill, outline_color=outline_color,
                                 line_width=line_width, font_obj=font_obj)
        # Determine a baseline for the bottom of the triangle.
        # (You may need to adjust this value to match your triangle's dimensions.)
        bottom_y = y + scale * 0.75  
        # Draw two horizontal lines at the bottom
        line_offset1 = scale * 0.05
        line_offset2 = scale * 0.1
        canvas.create_line(x - scale/2, bottom_y - line_offset1,
                           x + scale/2, bottom_y - line_offset1,
                           fill=outline_color, width=line_width)
        canvas.create_line(x - scale/2, bottom_y - line_offset2,
                           x + scale/2, bottom_y - line_offset2,
                           fill=outline_color, width=line_width)
        # Draw a small triangle on the right side as a clone indicator.
        tri_side = scale * 0.5
        tri_height = (math.sqrt(3) / 2) * tri_side
        att_x = x + scale  # position to the right of the main triangle
        att_y = y - tri_height / 2 - tri_height# adjust vertical position as needed
        v1 = (att_x, att_y)
        v2 = (att_x + tri_side, att_y)
        v3 = (att_x + tri_side/2, att_y - tri_height)
        canvas.create_polygon(v1, v2, v3, fill="lightblue", outline=outline_color,
                              width=line_width)

    def draw_shared_marker(self, canvas, x, y, zoom):
        """Draw a small shared marker at the given canvas coordinates."""
        size = 10 * zoom
        v1 = (x, y)
        v2 = (x - size, y)
        v3 = (x, y - size)
        canvas.create_polygon([v1, v2, v3], fill="black", outline="black")

    def draw_90_connection(self, canvas, parent_pt, child_pt, outline_color="dimgray", line_width=1, fixed_length=40):
        """Draw a 90° connection line from a parent point to a child point."""
        fixed_y = parent_pt[1] + fixed_length
        canvas.create_line(parent_pt[0], parent_pt[1], parent_pt[0], fixed_y,
                           fill=outline_color, width=line_width)
        canvas.create_line(parent_pt[0], fixed_y, child_pt[0], fixed_y,
                           fill=outline_color, width=line_width)
        canvas.create_line(child_pt[0], fixed_y, child_pt[0], child_pt[1],
                           fill=outline_color, width=line_width)

    def compute_rotated_and_gate_vertices(self, scale):
        """Compute vertices for a rotated AND gate shape scaled by 'scale'."""
        vertices = [(0, 0), (0, 2), (1, 2)]
        num_points = 50
        for i in range(num_points + 1):
            theta = math.pi / 2 - math.pi * i / num_points
            vertices.append((1 + math.cos(theta), 1 + math.sin(theta)))
        vertices.append((0, 0))
        def rotate_point(pt):
            x, y = pt
            return (2 - y, x)
        rotated = [rotate_point(pt) for pt in vertices]
        translated = [(vx + 2, vy + 1) for (vx, vy) in rotated]
        scaled = [(vx * scale, vy * scale) for (vx, vy) in translated]
        return scaled

    def draw_rotated_and_gate_shape(self, canvas, x, y, scale=40.0,
                                      top_text="Desc:\n\nRationale:",
                                      bottom_text="Event",
                                      fill="lightgray", outline_color="dimgray",
                                      line_width=1, font_obj=None):
        """Draw a rotated AND gate shape with top and bottom text labels."""
        if font_obj is None:
            font_obj = tkFont.Font(family="Arial", size=10)
        raw_verts = self.compute_rotated_and_gate_vertices(scale)
        flipped = [(vx, -vy) for (vx, vy) in raw_verts]
        xs = [v[0] for v in flipped]
        ys = [v[1] for v in flipped]
        cx, cy = (sum(xs) / len(xs), sum(ys) / len(ys))
        final_points = [(vx - cx + x, vy - cy + y) for (vx, vy) in flipped]
        canvas.create_polygon(final_points, fill=fill, outline=outline_color,
                                width=line_width, smooth=False)

        # Draw the top label box
        t_width, t_height = self.get_text_size(top_text, font_obj)
        padding = 6
        top_box_width = t_width + 2 * padding
        top_box_height = t_height + 2 * padding
        top_y = min(pt[1] for pt in final_points) - top_box_height - 5
        top_box_x = x - top_box_width / 2
        canvas.create_rectangle(top_box_x, top_y,
                                top_box_x + top_box_width,
                                top_y + top_box_height,
                                fill="lightblue", outline=outline_color,
                                width=line_width)
        canvas.create_text(top_box_x + top_box_width / 2,
                           top_y + top_box_height / 2,
                           text=top_text,
                           font=font_obj,
                           anchor="center",
                           width=top_box_width)

        # Draw the bottom label box
        b_width, b_height = self.get_text_size(bottom_text, font_obj)
        bottom_box_width = b_width + 2 * padding
        bottom_box_height = b_height + 2 * padding
        shape_lowest_y = max(pt[1] for pt in final_points)
        bottom_y = shape_lowest_y - (2 * bottom_box_height)
        bottom_box_x = x - bottom_box_width / 2
        canvas.create_rectangle(bottom_box_x, bottom_y,
                                bottom_box_x + bottom_box_width,
                                bottom_y + bottom_box_height,
                                fill="lightblue", outline=outline_color,
                                width=line_width)
        canvas.create_text(bottom_box_x + bottom_box_width / 2,
                           bottom_y + bottom_box_height / 2,
                           text=bottom_text,
                           font=font_obj,
                           anchor="center",
                           width=bottom_box_width)

    def draw_rotated_or_gate_shape(self, canvas, x, y, scale=40.0,
                                     top_text="Desc:\n\nRationale:",
                                     bottom_text="Event",
                                     fill="lightgray", outline_color="dimgray",
                                     line_width=1, font_obj=None):
        """Draw a rotated OR gate shape with text labels."""
        if font_obj is None:
            font_obj = tkFont.Font(family="Arial", size=10)
        def cubic_bezier(P0, P1, P2, P3, t):
            return ((1 - t) ** 3 * P0[0] + 3 * (1 - t) ** 2 * t * P1[0] +
                    3 * (1 - t) * t ** 2 * P2[0] + t ** 3 * P3[0],
                    (1 - t) ** 3 * P0[1] + 3 * (1 - t) ** 2 * t * P1[1] +
                    3 * (1 - t) * t ** 2 * P2[1] + t ** 3 * P3[1])
        num_points = 30
        t_values = [i / num_points for i in range(num_points + 1)]
        seg1 = [cubic_bezier((0, 0), (0.6, 0), (0.6, 2), (0, 2), t) for t in t_values]
        seg2 = [cubic_bezier((0, 2), (1, 2), (2, 1.6), (2, 1), t) for t in t_values]
        seg3 = [cubic_bezier((2, 1), (2, 0.4), (1, 0), (0, 0), t) for t in t_values]
        points = seg1[:-1] + seg2[:-1] + seg3
        rotated = [(2 - p[1], p[0]) for p in points]
        translated = [(pt[0] + 2, pt[1] + 1) for pt in rotated]
        scaled = [(sx * scale, sy * scale) for (sx, sy) in translated]
        flipped = [(vx, -vy) for (vx, vy) in scaled]
        xs = [p[0] for p in flipped]
        ys = [p[1] for p in flipped]
        cx, cy = (sum(xs) / len(xs), sum(ys) / len(ys))
        final_points = [(vx - cx + x, vy - cy + y) for (vx, vy) in flipped]
        canvas.create_polygon(final_points, fill=fill, outline=outline_color,
                                width=line_width, smooth=True)

        # Draw the top label box
        padding = 6
        t_width, t_height = self.get_text_size(top_text, font_obj)
        top_box_width = t_width + 2 * padding
        top_box_height = t_height + 2 * padding
        top_y = min(pt[1] for pt in final_points) - top_box_height - 5
        top_box_x = x - top_box_width / 2
        canvas.create_rectangle(top_box_x, top_y,
                                top_box_x + top_box_width,
                                top_y + top_box_height,
                                fill="lightblue", outline=outline_color, width=line_width)
        canvas.create_text(top_box_x + top_box_width / 2,
                           top_y + top_box_height / 2,
                           text=top_text, font=font_obj, anchor="center",
                           width=top_box_width)

        # Draw the bottom label box
        b_width, b_height = self.get_text_size(bottom_text, font_obj)
        bottom_box_width = b_width + 2 * padding
        bottom_box_height = b_height + 2 * padding
        shape_lowest_y = max(pt[1] for pt in final_points)
        bottom_y = shape_lowest_y - (2 * bottom_box_height)
        bottom_box_x = x - bottom_box_width / 2
        canvas.create_rectangle(bottom_box_x, bottom_y,
                                bottom_box_x + bottom_box_width,
                                bottom_y + bottom_box_height,
                                fill="lightblue", outline=outline_color,
                                width=line_width)
        canvas.create_text(bottom_box_x + bottom_box_width / 2,
                           bottom_y + bottom_box_height / 2,
                           text=bottom_text, font=font_obj,
                           anchor="center", width=bottom_box_width)

    def draw_rotated_and_gate_clone_shape(self, canvas, x, y, scale=40.0,
                                            top_text="Desc:\n\nRationale:", bottom_text="Node",
                                            fill="lightgray", outline_color="dimgray",
                                            line_width=1, font_obj=None):
        """Draw a rotated AND gate shape with additional clone details."""
        self.draw_rotated_and_gate_shape(canvas, x, y, scale=scale,
                                         top_text=top_text, bottom_text=bottom_text,
                                         fill=fill, outline_color=outline_color,
                                         line_width=line_width, font_obj=font_obj)
        bottom_y = y + scale * 1.5
        line_offset1 = scale * 0.05
        line_offset2 = scale * 0.1
        canvas.create_line(x - scale/2, bottom_y - line_offset1,
                           x + scale/2, bottom_y - line_offset1,
                           fill=outline_color, width=line_width)
        canvas.create_line(x - scale/2, bottom_y - line_offset2,
                           x + scale/2, bottom_y - line_offset2,
                           fill=outline_color, width=line_width)
        tri_side = scale * 0.5
        tri_height = (math.sqrt(3) / 2) * tri_side
        att_x = x + scale
        att_y = y - tri_height / 2
        v1 = (att_x, att_y)
        v2 = (att_x + tri_side, att_y)
        v3 = (att_x + tri_side / 2, att_y - tri_height)
        canvas.create_polygon(v1, v2, v3, fill="lightblue", outline=outline_color,
                              width=line_width)
        final_line_offset = scale * 0.15
        canvas.create_line(x - scale/2, bottom_y + final_line_offset,
                           x + scale/2, bottom_y + final_line_offset,
                           fill=outline_color, width=line_width)

    def draw_rotated_or_gate_clone_shape(self, canvas, x, y, scale=40.0,
                                           top_text="Desc:\n\nRationale:", bottom_text="Node",
                                           fill="lightgray", outline_color="dimgray",
                                           line_width=1, font_obj=None):
        """Draw a rotated OR gate shape with additional clone details."""
        self.draw_rotated_or_gate_shape(canvas, x, y, scale=scale,
                                        top_text=top_text, bottom_text=bottom_text,
                                        fill=fill, outline_color=outline_color,
                                        line_width=line_width, font_obj=font_obj)
        bottom_y = y + scale * 1.5
        line_offset1 = scale * 0.05
        line_offset2 = scale * 0.1
        canvas.create_line(x - scale/2, bottom_y - line_offset1,
                           x + scale/2, bottom_y - line_offset1,
                           fill=outline_color, width=line_width)
        canvas.create_line(x - scale/2, bottom_y - line_offset2,
                           x + scale/2, bottom_y - line_offset2,
                           fill=outline_color, width=line_width)
        tri_side = scale * 0.5
        tri_height = (math.sqrt(3) / 2) * tri_side
        att_x = x + scale
        att_y = y - tri_height / 2
        v1 = (att_x, att_y)
        v2 = (att_x + tri_side, att_y)
        v3 = (att_x + tri_side / 2, att_y - tri_height)
        canvas.create_polygon(v1, v2, v3, fill="lightblue",
                              outline=outline_color, width=line_width)
        final_line_offset = scale * 0.15
        canvas.create_line(x - scale/2, bottom_y + final_line_offset,
                           x + scale/2, bottom_y + final_line_offset,
                           fill=outline_color, width=line_width)

    def draw_triangle_shape(self, canvas, x, y, scale=40.0,
                              top_text="Desc:\n\nRationale:",
                              bottom_text="Event",
                              fill="lightgray", outline_color="dimgray",
                              line_width=1, font_obj=None):
        if font_obj is None:
            font_obj = tkFont.Font(family="Arial", size=10)
        effective_scale = scale * 2  
        h = effective_scale * math.sqrt(3) / 2
        v1 = (0, -2 * h / 3)
        v2 = (-effective_scale / 2, h / 3)
        v3 = (effective_scale / 2, h / 3)
        vertices = [(x + v1[0], y + v1[1]),
                    (x + v2[0], y + v2[1]),
                    (x + v3[0], y + v3[1])]
        canvas.create_polygon(vertices, fill=fill, outline=outline_color, width=line_width)
        
        t_width, t_height = self.get_text_size(top_text, font_obj)
        padding = 6
        top_box_width = t_width + 2 * padding
        top_box_height = t_height + 2 * padding
        top_box_x = x - top_box_width / 2
        top_box_y = min(v[1] for v in vertices) - top_box_height
        canvas.create_rectangle(top_box_x, top_box_y,
                                top_box_x + top_box_width,
                                top_box_y + top_box_height,
                                fill="lightblue", outline=outline_color, width=line_width)
        canvas.create_text(top_box_x + top_box_width / 2,
                           top_box_y + top_box_height / 2,
                           text=top_text,
                           font=font_obj, anchor="center", width=top_box_width)
        
        b_width, b_height = self.get_text_size(bottom_text, font_obj)
        bottom_box_width = b_width + 2 * padding
        bottom_box_height = b_height + 2 * padding
        bottom_box_x = x - bottom_box_width / 2
        bottom_box_y = max(v[1] for v in vertices) + padding - 2 * bottom_box_height
        canvas.create_rectangle(bottom_box_x, bottom_box_y,
                                bottom_box_x + bottom_box_width,
                                bottom_box_y + bottom_box_height,
                                fill="lightblue", outline=outline_color, width=line_width)
        canvas.create_text(bottom_box_x + bottom_box_width / 2,
                           bottom_box_y + bottom_box_height / 2,
                           text=bottom_text,
                           font=font_obj, anchor="center", width=bottom_box_width)
                           
    def draw_circle_event_shape(self, canvas, x, y, radius,
                                top_text="",
                                bottom_text="",
                                fill="lightyellow",
                                outline_color="dimgray",
                                line_width=1,
                                font_obj=None,
                                base_event=False):
        """Draw a circular event shape with optional text labels."""
        if font_obj is None:
            font_obj = tkFont.Font(family="Arial", size=10)
        left = x - radius
        top = y - radius
        right = x + radius
        bottom = y + radius
        canvas.create_oval(left, top, right, bottom, fill=fill,
                           outline=outline_color, width=line_width)
        t_width, t_height = self.get_text_size(top_text, font_obj)
        padding = 6
        top_box_width = t_width + 2 * padding
        top_box_height = t_height + 2 * padding
        top_box_x = x - top_box_width / 2
        top_box_y = top - top_box_height
        canvas.create_rectangle(top_box_x, top_box_y,
                                top_box_x + top_box_width,
                                top_box_y + top_box_height,
                                fill="lightblue", outline=outline_color,
                                width=line_width)
        canvas.create_text(top_box_x + top_box_width / 2,
                           top_box_y + top_box_height / 2,
                           text=top_text,
                           font=font_obj, anchor="center",
                           width=top_box_width)
        b_width, b_height = self.get_text_size(bottom_text, font_obj)
        bottom_box_width = b_width + 2 * padding
        bottom_box_height = b_height + 2 * padding
        bottom_box_x = x - bottom_box_width / 2
        bottom_box_y = bottom - 2 * bottom_box_height
        canvas.create_rectangle(bottom_box_x, bottom_box_y,
                                bottom_box_x + bottom_box_width,
                                bottom_box_y + bottom_box_height,
                                fill="lightblue", outline=outline_color,
                                width=line_width)
        canvas.create_text(bottom_box_x + bottom_box_width / 2,
                           bottom_box_y + bottom_box_height / 2,
                           text=bottom_text,
                           font=font_obj, anchor="center",
                           width=bottom_box_width)
                           
    def draw_triangle_clone_shape(self, canvas, x, y, scale=40.0,
                                  top_text="Desc:\n\nRationale:", bottom_text="Node",
                                  fill="lightgray", outline_color="dimgray",
                                  line_width=1, font_obj=None):
        """
        Draws the same triangle as draw_triangle_shape but then adds two horizontal lines
        at the bottom and a small triangle on the right side as clone indicators.
        The small triangle is now positioned so that its top vertex aligns with the top of
        the big triangle.
        """
        if font_obj is None:
            font_obj = tkFont.Font(family="Arial", size=10)
        # Draw the base triangle.
        self.draw_triangle_shape(canvas, x, y, scale=scale,
                                 top_text=top_text, bottom_text=bottom_text,
                                 fill=fill, outline_color=outline_color,
                                 line_width=line_width, font_obj=font_obj)
        # Compute the vertices of the big triangle.
        effective_scale = scale * 2  
        h = effective_scale * math.sqrt(3) / 2
        v1 = (0, -2 * h / 3)
        v2 = (-effective_scale / 2, h / 3)
        v3 = (effective_scale / 2, h / 3)
        vertices = [(x + v1[0], y + v1[1]),
                    (x + v2[0], y + v2[1]),
                    (x + v3[0], y + v3[1])]
        # Compute the bottom and top y-values of the big triangle.
        bottom_y = max(v[1] for v in vertices) + scale * 0.2
        top_y = min(v[1] for v in vertices)  # top edge of the big triangle
        half_width = effective_scale / 2  # equals 'scale'
        
        # Draw two horizontal lines at the bottom (unchanged).
        line_offset1 = scale * 0.05
        line_offset2 = scale * 0.1
        canvas.create_line(x - half_width, bottom_y - line_offset1,
                           x + half_width, bottom_y - line_offset1,
                           fill=outline_color, width=line_width)
        canvas.create_line(x - half_width, bottom_y - line_offset2,
                           x + half_width, bottom_y - line_offset2,
                           fill=outline_color, width=line_width)
        
        # Draw the small clone indicator triangle.
        tri_side = scale * 0.5
        tri_height = (math.sqrt(3) / 2) * tri_side
        att_x = x + half_width
        # Instead of basing its vertical position on bottom_y, we now align it with top_y.
        # We want the top vertex of the small triangle (which is at att_y - tri_height)
        # to equal top_y. Thus, set att_y - tri_height = top_y, so:
        att_y = top_y + tri_height
        v1_small = (att_x, att_y)
        v2_small = (att_x + tri_side, att_y)
        v3_small = (att_x + tri_side/2, att_y - tri_height)
        canvas.create_polygon(v1_small, v2_small, v3_small,
                              fill="lightblue", outline=outline_color,
                              width=line_width)
        
        # Draw the final horizontal line below the bottom.
        final_line_offset = scale * 0.15
        canvas.create_line(x - half_width, bottom_y + final_line_offset,
                           x + half_width, bottom_y + final_line_offset,
                           fill=outline_color, width=line_width)
                           
# Create a single FTADrawingHelper object that can be used by other classes
fta_drawing_helper = FTADrawingHelper()
AD_RiskAssessment_Helper = ADRiskAssessmentHelper()

##########################################
# Edit Dialog 
##########################################
class EditNodeDialog(simpledialog.Dialog):
    def __init__(self, parent, node, app):
        self.node = node
        self.app = app
        super().__init__(parent, title="Edit Node")

    def body(self, master):
        dialog_font = tkFont.Font(family="Arial", size=10)
        ttk.Label(master, text="Node ID:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_entry = tk.Entry(master, font=dialog_font, state="disabled")
        self.id_entry.insert(0, f"Node {self.node.unique_id}")
        self.id_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(master, text="User Name:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.user_name_entry = tk.Entry(master, font=dialog_font)
        self.user_name_entry.insert(0, self.node.user_name)
        self.user_name_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(master, text="Description:").grid(row=2, column=0, padx=5, pady=5, sticky="ne")
        self.desc_text = tk.Text(master, width=40, height=3, font=dialog_font, wrap="word")
        self.desc_text.insert("1.0", self.node.description)
        self.desc_text.grid(row=2, column=1, padx=5, pady=5)
        self.desc_text.bind("<Return>", self.on_enter_pressed)

        ttk.Label(master, text="\nRationale:").grid(row=3, column=0, padx=5, pady=5, sticky="ne")
        self.rationale_text = tk.Text(master, width=40, height=3, font=dialog_font, wrap="word")
        self.rationale_text.insert("1.0", self.node.rationale)
        self.rationale_text.grid(row=3, column=1, padx=5, pady=5)
        self.rationale_text.bind("<Return>", self.on_enter_pressed)

        row_next = 4
        if self.node.node_type.upper() in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
            ttk.Label(master, text="Value (1-5):").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
            self.value_combo = ttk.Combobox(master, values=["1", "2", "3", "4", "5"],
                                            state="readonly", width=5, font=dialog_font)
            current_val = self.node.quant_value if self.node.quant_value is not None else 1
            self.value_combo.set(str(int(current_val)))
            self.value_combo.grid(row=row_next, column=1, padx=5, pady=5)
            row_next += 1

            # NEW: Safety Requirements Section for base nodes.
            # Ensure the node has the attribute.
            if not hasattr(self.node, "safety_requirements"):
                self.node.safety_requirements = []
            ttk.Label(master, text="Safety Requirements:").grid(row=row_next, column=0, padx=5, pady=5, sticky="ne")
            self.safety_req_frame = ttk.Frame(master)
            self.safety_req_frame.grid(row=row_next, column=1, padx=5, pady=5, sticky="w")
            row_next += 1

            # Create a listbox to display safety requirements.
            self.safety_req_listbox = tk.Listbox(self.safety_req_frame, height=4, width=50)
            self.safety_req_listbox.grid(row=0, column=0, columnspan=3, sticky="w")
            # Populate listbox with existing requirements.
            for req in self.node.safety_requirements:
                self.safety_req_listbox.insert(tk.END, f"[{req['id']}] [{req['req_type']}] [{req.get('asil','')}] {req['text']}")

            # Buttons for Add, Edit, and Delete.
            self.add_req_button = ttk.Button(self.safety_req_frame, text="Add New", command=self.add_safety_requirement)
            self.add_req_button.grid(row=1, column=0, padx=2, pady=2)
            self.edit_req_button = ttk.Button(self.safety_req_frame, text="Edit", command=self.edit_safety_requirement)
            self.edit_req_button.grid(row=1, column=1, padx=2, pady=2)
            self.delete_req_button = ttk.Button(self.safety_req_frame, text="Delete", command=self.delete_safety_requirement)
            self.delete_req_button.grid(row=1, column=2, padx=2, pady=2)
            self.add_existing_req_button = ttk.Button(self.safety_req_frame, text="Add Existing", command=self.add_existing_requirement)
            self.add_existing_req_button.grid(row=1, column=3, padx=2, pady=2)

        elif self.node.node_type.upper() == "BASIC EVENT":
            ttk.Label(master, text="Failure Probability:").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
            self.prob_entry = tk.Entry(master, font=dialog_font)
            self.prob_entry.insert(0, str(self.node.failure_prob))
            self.prob_entry.grid(row=row_next, column=1, padx=5, pady=5)
            row_next += 1

            if not hasattr(self.node, "safety_requirements"):
                self.node.safety_requirements = []
            ttk.Label(master, text="Safety Requirements:").grid(row=row_next, column=0, padx=5, pady=5, sticky="ne")
            self.safety_req_frame = ttk.Frame(master)
            self.safety_req_frame.grid(row=row_next, column=1, padx=5, pady=5, sticky="w")
            row_next += 1

            self.safety_req_listbox = tk.Listbox(self.safety_req_frame, height=4, width=50)
            self.safety_req_listbox.grid(row=0, column=0, columnspan=3, sticky="w")
            for req in self.node.safety_requirements:
                self.safety_req_listbox.insert(tk.END, f"[{req['id']}] [{req['req_type']}] [{req.get('asil','')}] {req['text']}")
            self.add_req_button = ttk.Button(self.safety_req_frame, text="Add New", command=self.add_safety_requirement)
            self.add_req_button.grid(row=1, column=0, padx=2, pady=2)
            self.edit_req_button = ttk.Button(self.safety_req_frame, text="Edit", command=self.edit_safety_requirement)
            self.edit_req_button.grid(row=1, column=1, padx=2, pady=2)
            self.delete_req_button = ttk.Button(self.safety_req_frame, text="Delete", command=self.delete_safety_requirement)
            self.delete_req_button.grid(row=1, column=2, padx=2, pady=2)
            self.add_existing_req_button = ttk.Button(self.safety_req_frame, text="Add Existing", command=self.add_existing_requirement)
            self.add_existing_req_button.grid(row=1, column=3, padx=2, pady=2)

        elif self.node.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
            ttk.Label(master, text="Gate Type:").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
            self.gate_var = tk.StringVar(value=self.node.gate_type if self.node.gate_type else "AND")
            self.gate_combo = ttk.Combobox(master, textvariable=self.gate_var, values=["AND", "OR"],
                                           state="readonly", width=10)
            self.gate_combo.grid(row=row_next, column=1, padx=5, pady=5)
            row_next += 1
            if self.node.node_type.upper() == "TOP EVENT":
                ttk.Label(master, text="Severity (1-5):").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
                self.sev_combo = ttk.Combobox(master, values=["1", "2", "3", "4", "5"],
                                              state="readonly", width=5, font=dialog_font)
                current_sev = self.node.severity if self.node.severity is not None else 5
                self.sev_combo.set(str(int(current_sev)))
                self.sev_combo.grid(row=row_next, column=1, padx=5, pady=5)
                row_next += 1

                ttk.Label(master, text="Controllability (1-5):").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
                self.cont_combo = ttk.Combobox(master, values=["1", "2", "3", "4", "5"],
                                              state="readonly", width=5, font=dialog_font)
                current_cont = self.node.controllability if self.node.controllability is not None else 3
                self.cont_combo.set(str(int(current_cont)))
                self.cont_combo.grid(row=row_next, column=1, padx=5, pady=5)
                row_next += 1

                ttk.Label(master, text="Safety Goal Description:").grid(row=row_next, column=0, padx=5, pady=5, sticky="ne")
                self.safety_goal_text = tk.Text(master, width=40, height=3, font=dialog_font, wrap="word")
                self.safety_goal_text.insert("1.0", self.node.safety_goal_description)
                self.safety_goal_text.grid(row=row_next, column=1, padx=5, pady=5)
                self.safety_goal_text.bind("<Return>", self.on_enter_pressed)
                row_next += 1

                ttk.Label(master, text="Safety Goal ASIL:").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
                self.sg_asil_var = tk.StringVar(value=self.node.safety_goal_asil if self.node.safety_goal_asil else "QM")
                self.sg_asil_combo = ttk.Combobox(
                    master,
                    textvariable=self.sg_asil_var,
                    values=ASIL_LEVEL_OPTIONS,
                    state="readonly",
                    width=8,
                )
                self.sg_asil_combo.grid(row=row_next, column=1, padx=5, pady=5, sticky="w")
                row_next += 1


        if self.node.node_type.upper() not in ["TOP EVENT", "BASIC EVENT"]:
            self.is_page_var = tk.BooleanVar(value=self.node.is_page)
            ttk.Checkbutton(master, text="Is Page Gate?", variable=self.is_page_var)\
                .grid(row=row_next, column=0, columnspan=2, padx=5, pady=5, sticky="w")
            row_next += 1

        if "CONFIDENCE" in self.node.node_type.upper():
            base_name = "Confidence"
        elif "ROBUSTNESS" in self.node.node_type.upper():
            base_name = "Robustness"
        elif "TOP EVENT" in self.node.node_type.upper():
            base_name = "Prototype Assurance Level (PAL)"
        elif "GATE" in self.node.node_type.upper() or "RIGOR" in self.node.node_type.upper():
            base_name = "Rigor"
        else:
            base_name = "Other"

        if self.node.display_label.startswith("Maturity"):
            base_name = "Maturity"

        valid_subtypes = VALID_SUBTYPES.get(base_name, [])
        if not valid_subtypes:
            valid_subtypes = ["None"]
        ttk.Label(master, text="Subtype:").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
        initial_subtype = self.node.input_subtype if self.node.input_subtype else valid_subtypes[0]
        self.subtype_var = tk.StringVar(value=initial_subtype)
        state = "disabled" if base_name == "Maturity" else "readonly"
        self.subtype_combo = ttk.Combobox(master, textvariable=self.subtype_var, values=valid_subtypes,
                                          state=state, width=20)
        self.subtype_combo.grid(row=row_next, column=1, padx=5, pady=5, sticky="w")
        row_next += 1

        return self.user_name_entry

    class RequirementDialog(simpledialog.Dialog):
        def __init__(self, parent, title, initial_req=None):
            self.initial_req = initial_req or {}
            super().__init__(parent, title=title)
        
        def body(self, master):
            # Instead of master.resizable(), use self.top
            self.resizable(False, False)
            dialog_font = tk.font.Font(family="Arial", size=10)
            ttk.Label(master, text="Requirement Type:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
            self.type_var = tk.StringVar()
            self.type_combo = ttk.Combobox(master, textvariable=self.type_var, 
                                           values=["vehicle", "operational"],
                                           state="readonly", width=15)
            self.type_combo.grid(row=0, column=1, padx=5, pady=5)
            
            ttk.Label(master, text="Custom Requirement ID:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
            self.custom_id_entry = tk.Entry(master, width=20, font=dialog_font)
            # Preload using "custom_id" if available; otherwise, fallback to "id"
            self.custom_id_entry.insert(0, self.initial_req.get("custom_id") or self.initial_req.get("id", ""))
            self.custom_id_entry.grid(row=1, column=1, padx=5, pady=5)

            ttk.Label(master, text="Requirement Text:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
            self.req_entry = tk.Entry(master, width=40, font=dialog_font)
            self.req_entry.grid(row=2, column=1, padx=5, pady=5)

            ttk.Label(master, text="ASIL:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
            self.req_asil_var = tk.StringVar()
            self.req_asil_combo = ttk.Combobox(
                master,
                textvariable=self.req_asil_var,
                values=ASIL_LEVEL_OPTIONS,
                state="readonly",
                width=8,
            )
            self.req_asil_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")

            self.type_var.set(self.initial_req.get("req_type", "vehicle"))
            self.req_entry.insert(0, self.initial_req.get("text", ""))
            self.req_asil_var.set(self.initial_req.get("asil", "QM"))
            return self.req_entry

        def apply(self):
            req_type = self.type_var.get().strip()
            req_text = self.req_entry.get().strip()
            custom_id = self.custom_id_entry.get().strip()
            asil = self.req_asil_var.get().strip()
            self.result = {"req_type": req_type, "text": req_text, "custom_id": custom_id, "asil": asil}

        def validate(self):
            custom_id = self.custom_id_entry.get().strip()
            # If a custom ID is provided, ensure it's unique unless we're editing this requirement
            if custom_id:
                existing = global_requirements.get(custom_id)
                if existing and custom_id not in (
                    self.initial_req.get("custom_id"),
                    self.initial_req.get("id"),
                ):
                    messagebox.showerror(
                        "Duplicate ID",
                        f"Requirement ID '{custom_id}' already exists. Please choose a unique ID.",
                    )
                    return False
            return True

    class SelectExistingRequirementsDialog(simpledialog.Dialog):
        """
        A dialog that displays all global requirements in a list with checkboxes.
        The user can select one or more existing requirements to add (as clones) to the current node.
        """
        def __init__(self, parent, title="Select Existing Requirements"):
            # We'll use a dict to track checkbox variables keyed by requirement ID.
            self.selected_vars = {}
            super().__init__(parent, title=title)

        def body(self, master):
            ttk.Label(master, text="Select one or more existing requirements:").pack(padx=5, pady=5)

            # Create a container canvas and a vertical scrollbar
            container = ttk.Frame(master)
            container.pack(fill=tk.BOTH, expand=True)

            canvas = tk.Canvas(container, borderwidth=0)
            scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
            self.check_frame = ttk.Frame(canvas)

            # Configure the scrollable region when the frame's size changes
            self.check_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=self.check_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Pack canvas and scrollbar side by side
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # For each requirement in the global registry, create a Checkbutton.
            for req_id, req in global_requirements.items():
                var = tk.BooleanVar(value=False)
                self.selected_vars[req_id] = var
                text = f"[{req['id']}] [{req['req_type']}] [{req.get('asil','')}] {req['text']}"
                ttk.Checkbutton(self.check_frame, text=text, variable=var).pack(anchor="w", padx=2, pady=2)
            return self.check_frame

        def apply(self):
            # Return a list of requirement IDs that were selected.
            self.result = [req_id for req_id, var in self.selected_vars.items() if var.get()]

    def add_existing_requirement(self):
        """
        Opens a dialog to let the user select one or more existing requirements from the global registry.
        The selected requirements are then allocated to the current node (as clones sharing the same custom ID).
        """
        global global_requirements  # Ensure we refer to the module-level variable
        if not global_requirements:
            messagebox.showinfo("No Existing Requirements", "There are no existing requirements to add.")
            return
        dialog = self.SelectExistingRequirementsDialog(self, title="Select Existing Requirements")
        if dialog.result:
            # For each selected requirement, allocate it to the node if not already present.
            if not hasattr(self.node, "safety_requirements"):
                self.node.safety_requirements = []
            for req_id in dialog.result:
                req = global_requirements.get(req_id)
                if req and not any(r["id"] == req_id for r in self.node.safety_requirements):
                    # For clone semantics, we simply add the same dictionary reference.
                    self.node.safety_requirements.append(req)
                    self.safety_req_listbox.insert(tk.END, f"[{req['id']}] [{req['req_type']}] [{req.get('asil','')}] {req['text']}")
        else:
            messagebox.showinfo("No Selection", "No existing requirements were selected.")
   
    def add_new_requirement(self,custom_id, req_type, text, asil="QM"):
        # When a requirement is created, register it in the global registry.
        req = {"id": custom_id, "req_type": req_type, "text": text, "custom_id": custom_id, "asil": asil}
        global_requirements[custom_id] = req
        print(f"Added new requirement: {req}")
        return req
        
    def list_all_requirements(self):
        # This function returns a list of formatted strings for all requirements
        return [f"[{req['id']}] [{req['req_type']}] [{req.get('asil','')}] {req['text']}" for req in global_requirements.values()]
    
    def add_safety_requirement(self):
        """
        Opens the custom dialog to create a new requirement.
        Also, provides a button (or similar mechanism) to add existing requirements.
        """
        global global_requirements  # Ensure we refer to the module-level global_requirements
        # Use self.master (the Toplevel parent of this dialog) instead of self.
        dialog = self.RequirementDialog(self.master, title="Add Safety Requirement")
        if dialog.result is None or dialog.result["text"] == "":
            return
        custom_id = dialog.result.get("custom_id", "").strip()
        if not custom_id:
            custom_id = str(uuid.uuid4())
        # Check global registry: if exists, update; otherwise, register new.
        if custom_id in global_requirements:
            req = global_requirements[custom_id]
            req["req_type"] = dialog.result["req_type"]
            req["text"] = dialog.result["text"]
            req["asil"] = dialog.result.get("asil", "QM")
        else:
            req = {
                "id": custom_id,
                "req_type": dialog.result["req_type"],
                "text": dialog.result["text"],
                "custom_id": custom_id,
                "asil": dialog.result.get("asil", "QM")
            }
            global_requirements[custom_id] = req

        # Allocate this requirement to the current node if not already present.
        if not hasattr(self.node, "safety_requirements"):
            self.node.safety_requirements = []
        if not any(r["id"] == custom_id for r in self.node.safety_requirements):
            self.node.safety_requirements.append(req)
            self.safety_req_listbox.insert(tk.END, f"[{req['id']}] [{req['req_type']}] [{req.get('asil','')}] {req['text']}")

    def edit_safety_requirement(self):
        """
        Opens the edit dialog for a selected safety requirement.
        After editing, updates the global registry so that all nodes sharing that requirement are synchronized.
        """
        selected = self.safety_req_listbox.curselection()
        if not selected:
            messagebox.showwarning("Edit Requirement", "Select a requirement to edit.")
            return
        index = selected[0]
        current_req = self.node.safety_requirements[index]
        initial_req = current_req.copy()
        # Pass self.master as the parent here as well.
        dialog = self.RequirementDialog(self.master, title="Edit Safety Requirement", initial_req=initial_req)
        if dialog.result is None or dialog.result["text"] == "":
            return
        new_custom_id = dialog.result["custom_id"].strip() or current_req.get("custom_id") or current_req.get("id") or str(uuid.uuid4())
        current_req["req_type"] = dialog.result["req_type"]
        current_req["text"] = dialog.result["text"]
        current_req["asil"] = dialog.result.get("asil", "QM")
        current_req["custom_id"] = new_custom_id
        current_req["id"] = new_custom_id
        global_requirements[new_custom_id] = current_req
        self.node.safety_requirements[index] = current_req
        self.safety_req_listbox.delete(index)
        self.safety_req_listbox.insert(index, f"[{current_req['id']}] [{current_req['req_type']}] [{current_req.get('asil','')}] {current_req['text']}")

    def delete_safety_requirement(self):
        selected = self.safety_req_listbox.curselection()
        if not selected:
            messagebox.showwarning("Delete Requirement", "Select a requirement to delete.")
            return
        index = selected[0]
        del self.node.safety_requirements[index]
        self.safety_req_listbox.delete(index)

    def buttonbox(self):
        box = tk.Frame(self)
        ok_button = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
        ok_button.pack(side=tk.LEFT, padx=5, pady=5)
        cancel_button = tk.Button(box, text="Cancel", width=10, command=self.cancel)
        cancel_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.bind("<Escape>", lambda event: self.cancel())
        box.pack()

    def on_enter_pressed(self, event):
        event.widget.insert("insert", "\n")
        return "break"

    def validate(self):
        return True

    def apply(self):
        target_node = self.node if self.node.is_primary_instance else self.node.original

        target_node.user_name = self.user_name_entry.get().strip()
        target_node.description = self.desc_text.get("1.0", "end-1c")
        target_node.rationale = self.rationale_text.get("1.0", "end-1c")
        
        if self.node.node_type.upper() in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
            try:
                val = float(self.value_combo.get().strip())
                if not (1 <= val <= 5):
                    raise ValueError
                target_node.quant_value = val
            except ValueError:
                messagebox.showerror("Invalid Input", "Select a value between 1 and 5.")
        elif self.node.node_type.upper() == "BASIC EVENT":
            try:
                prob = float(self.prob_entry.get().strip())
                if prob < 0:
                    raise ValueError
                target_node.failure_prob = prob
            except ValueError:
                messagebox.showerror("Invalid Input", "Enter a valid probability")
        elif self.node.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
            target_node.gate_type = self.gate_var.get().strip().upper()
            if self.node.node_type.upper() == "TOP EVENT":
                try:
                    sev = float(self.sev_combo.get().strip())
                    if not (1 <= sev <= 5):
                        raise ValueError
                    target_node.severity = sev
                except ValueError:
                    messagebox.showerror("Invalid Input", "Select a severity between 1 and 5.")
                try:
                    cont = float(self.cont_combo.get().strip())
                    if not (1 <= cont <= 5):
                        raise ValueError
                    target_node.controllability = cont
                except ValueError:
                    messagebox.showerror("Invalid Input", "Select a controllability between 1 and 5.")
                target_node.is_page = False
                target_node.safety_goal_description = self.safety_goal_text.get("1.0", "end-1c")
                target_node.safety_goal_asil = self.sg_asil_var.get().strip()
            else:
                target_node.is_page = self.is_page_var.get()

        if hasattr(self, "subtype_var"):
            target_node.input_subtype = self.subtype_var.get()

        self.app.sync_nodes_by_id(target_node)
        AD_RiskAssessment_Helper.calculate_assurance_recursive(
            self.app.root_node,
            self.app.top_events,
        )
        self.app.update_views()

##########################################
# Main Application (Parent Diagram)
##########################################
class FaultTreeApp:
    def __init__(self, root):
        self.root = root
        self.top_events = []
        self.selected_node = None
        self.clone_offset_counter = {}
        self.root.title("Autonomous Driving Risk Assessment")
        self.zoom = 1.0
        self.diagram_font = tkFont.Font(family="Arial", size=int(8 * self.zoom))
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("Treeview", font=("Arial", 10))
        self.clipboard_node = None
        self.cut_mode = False
        self.page_history = []
        self.project_properties = {"pdf_report_name": "Autonomous Driving Risk Assessment PDF Report"}
        self.top_events = []
        self.reviews = []
        self.review_data = None
        self.review_window = None
        self.current_user = ""
        self.comment_target = None
        self.versions = []
        self.diff_nodes = []
        # Provide the drawing helper to dialogs that may be opened later
        self.fta_drawing_helper = fta_drawing_helper

        menubar = tk.Menu(root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_model, accelerator="Ctrl+N")
        file_menu.add_command(label="Save Model", command=self.save_model, accelerator="Ctrl+S")
        file_menu.add_command(label="Load Model", command=self.load_model, accelerator="Ctrl+O")
        file_menu.add_command(label="FMEA Manager", command=self.show_fmea_list)
        file_menu.add_command(label="New Vehicle Level Function", command=self.add_top_level_event)
        file_menu.add_command(label="Project Properties", command=self.edit_project_properties)
        file_menu.add_command(label="Save PDF Report", command=self.generate_pdf_report)
        file_menu.add_command(label="Save PDF Without Assurance", command=self.generate_pdf_without_assurance)
        file_menu.add_command(label="Export SG Requirements", command=self.export_safety_goal_requirements)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.confirm_close)
        menubar.add_cascade(label="File", menu=file_menu)
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Add Confidence", command=lambda: self.add_node_of_type("Confidence Level"), accelerator="Ctrl+Shift+C")
        edit_menu.add_command(label="Add Robustness", command=lambda: self.add_node_of_type("Robustness Score"), accelerator="Ctrl+Shift+R")
        edit_menu.add_command(label="Add Gate", command=lambda: self.add_node_of_type("GATE"), accelerator="Ctrl+Shift+G")
        edit_menu.add_command(label="Add Basic Event", command=lambda: self.add_node_of_type("Basic Event"), accelerator="Ctrl+Shift+B")
        edit_menu.add_command(label="Edit Selected", command=self.edit_selected)
        edit_menu.add_command(label="Remove Connection", command=lambda: self.remove_connection(self.selected_node) if self.selected_node else None)
        edit_menu.add_command(label="Delete Node", command=lambda: self.delete_node_and_subtree(self.selected_node) if self.selected_node else None)
        edit_menu.add_command(label="Remove Node", command=self.remove_node)
        edit_menu.add_separator()
        edit_menu.add_command(label="Copy", command=self.copy_node, accelerator="Ctrl+C")
        edit_menu.add_command(label="Cut", command=self.cut_node, accelerator="Ctrl+X")
        edit_menu.add_command(label="Paste", command=self.paste_node, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Edit User Name", command=self.edit_user_name, accelerator="Ctrl+U")
        edit_menu.add_command(label="Edit Description", command=self.edit_description, accelerator="Ctrl+D")
        edit_menu.add_command(label="Edit Rationale", command=self.edit_rationale, accelerator="Ctrl+L")
        edit_menu.add_command(label="Edit Value", command=self.edit_value)
        edit_menu.add_command(label="Edit Gate Type", command=self.edit_gate_type, accelerator="Ctrl+G")
        edit_menu.add_command(label="Edit Severity", command=self.edit_severity, accelerator="Ctrl+E")
        edit_menu.add_command(label="Edit Controllability", command=self.edit_controllability)
        edit_menu.add_command(label="Edit Page Flag", command=self.edit_page_flag)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        process_menu = tk.Menu(menubar, tearoff=0)
        process_menu.add_command(label="Calc Prototype Assurance Level (PAL)", command=self.calculate_overall, accelerator="Ctrl+R")
        process_menu.add_command(label="Calc PMHF", command=self.calculate_pmfh, accelerator="Ctrl+M")
        menubar.add_cascade(label="Process", menu=process_menu)
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Auto Arrange", command=self.auto_arrange, accelerator="Ctrl+A")
        view_menu.add_command(label="Requirements Matrix", command=self.show_requirements_matrix)
        view_menu.add_command(label="FTA-FMEA Traceability", command=self.show_traceability_matrix)
        view_menu.add_command(label="Safety Goals Matrix", command=self.show_safety_goals_matrix)
        menubar.add_cascade(label="View", menu=view_menu)
        review_menu = tk.Menu(menubar, tearoff=0)
        review_menu.add_command(label="Start Peer Review", command=self.start_peer_review)
        review_menu.add_command(label="Start Joint Review", command=self.start_joint_review)
        review_menu.add_command(label="Open Review Toolbox", command=self.open_review_toolbox)
        review_menu.add_command(label="Set Current User", command=self.set_current_user)
        review_menu.add_command(label="Merge Review Comments", command=self.merge_review_comments)
        review_menu.add_command(label="Compare Versions", command=self.compare_versions)
        menubar.add_cascade(label="Review", menu=review_menu)
        root.config(menu=menubar)
        root.bind("<Control-n>", lambda event: self.new_model())
        root.bind("<Control-s>", lambda event: self.save_model())
        root.bind("<Control-o>", lambda event: self.load_model())
        root.bind("<Control-r>", lambda event: self.calculate_overall())
        root.bind("<Control-m>", lambda event: self.calculate_pmfh())
        root.bind("<Control-=>", lambda event: self.zoom_in())
        root.bind("<Control-minus>", lambda event: self.zoom_out())
        root.bind("<Control-a>", lambda event: self.auto_arrange())
        root.bind("<Control-u>", lambda event: self.edit_user_name())
        root.bind("<Control-d>", lambda event: self.edit_description())
        root.bind("<Control-l>", lambda event: self.edit_rationale())
        root.bind("<Control-g>", lambda event: self.edit_gate_type())
        root.bind("<Control-e>", lambda event: self.edit_severity())
        root.bind("<Control-Shift-c>", lambda event: self.add_node_of_type("Confidence Level"))
        root.bind("<Control-Shift-r>", lambda event: self.add_node_of_type("Robustness Score"))
        root.bind("<Control-Shift-g>", lambda event: self.add_node_of_type("GATE"))
        root.bind("<Control-Shift-b>", lambda event: self.add_node_of_type("Basic Event"))
        root.bind("<Control-c>", lambda event: self.copy_node())
        root.bind("<Control-x>", lambda event: self.cut_node())
        root.bind("<Control-v>", lambda event: self.paste_node())
        root.bind("<Control-p>", lambda event: self.save_diagram_png())
        self.main_pane = tk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)
        self.tree_frame = ttk.Frame(self.main_pane)

        self.top_event_controls = ttk.Frame(self.tree_frame)
        self.top_event_controls.pack(side=tk.TOP, fill=tk.X)

        self.move_up_btn = ttk.Button(self.top_event_controls, text="Move Up", command=self.move_top_event_up)
        self.move_up_btn.pack(side=tk.LEFT, padx=2)
        self.move_down_btn = ttk.Button(self.top_event_controls, text="Move Down", command=self.move_top_event_down)
        self.move_down_btn.pack(side=tk.LEFT, padx=2)

        
        self.treeview = ttk.Treeview(self.tree_frame)
        self.treeview.pack(fill=tk.BOTH, expand=True)
        self.treeview.bind("<Double-1>", lambda e: self.edit_selected())
        self.treeview.bind("<ButtonRelease-1>", self.on_treeview_click)
        self.main_pane.add(self.tree_frame, width=300)
        self.canvas_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(self.canvas_frame, stretch="always")
        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.hbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.vbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set,
                           scrollregion=(0, 0, 2000, 2000))
        self.canvas.bind("<ButtonPress-3>", self.on_right_mouse_press)
        self.canvas.bind("<B3-Motion>", self.on_right_mouse_drag)
        self.canvas.bind("<ButtonRelease-3>", self.show_context_menu)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_mousewheel)
        self.root_node = FaultTreeNode("", "TOP EVENT")
        self.root_node.x, self.root_node.y = 300, 200
        self.top_events = [self.root_node]
        self.fmea_entries = []
        self.fmeas = []  # list of FMEA documents
        self.selected_node = None
        self.dragging_node = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.grid_size = 20
        self.update_views()
        # Track the last saved state so we can prompt on exit
        self.last_saved_state = json.dumps(self.export_model_data(), sort_keys=True)
        root.protocol("WM_DELETE_WINDOW", self.confirm_close)

    def generate_recommendations_for_top_event(self, node):
        # Determine the Prototype Assurance Level (PAL) based on the node’s quantitative score.
        level = AD_RiskAssessment_Helper.discretize_level(node.quant_value) if node.quant_value is not None else 1
        rec = dynamic_recommendations.get(level, {})
        rec_text = f"<b>Recommendations for Prototype Assurance Level (PAL) {level}:</b><br/>"
        for category in ["Testing Requirements", "IFTD Responsibilities", "Preventive Maintenance Actions", "Relevant AVSC Guidelines"]:
            if category in rec:
                rec_text += f"<b>{category}:</b><br/><ul><li>{rec[category]}</li></ul><br/>"
        return rec_text

    def back_all_pages(self):
        if self.page_history:
            # Jump to the very first page saved in history:
            first_page = self.page_history[0]
            # Clear the history so that subsequent back presses do not try to go further.
            self.page_history = []
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()
            self.open_page_diagram(first_page)
        else:
            # No history: you could simply reinitialize the main diagram
            self.close_page_diagram()

    def move_top_event_up(self):
        sel = self.treeview.selection()
        if not sel:
            messagebox.showwarning("Move Up", "Select a top-level event to move.")
            return
        try:
            node_id = int(self.treeview.item(sel[0], "tags")[0])
        except Exception:
            return
        # Find the index in the top_events list.
        index = next((i for i, event in enumerate(self.top_events) if event.unique_id == node_id), None)
        if index is None:
            messagebox.showwarning("Move Up", "The selected node is not a top-level event.")
            return
        if index == 0:
            messagebox.showinfo("Move Up", "This event is already at the top.")
            return
        # Swap with the one above it.
        self.top_events[index], self.top_events[index - 1] = self.top_events[index - 1], self.top_events[index]
        self.update_views()

    def move_top_event_down(self):
        sel = self.treeview.selection()
        if not sel:
            messagebox.showwarning("Move Down", "Select a top-level event to move.")
            return
        try:
            node_id = int(self.treeview.item(sel[0], "tags")[0])
        except Exception:
            return
        index = next((i for i, event in enumerate(self.top_events) if event.unique_id == node_id), None)
        if index is None:
            messagebox.showwarning("Move Down", "The selected node is not a top-level event.")
            return
        if index == len(self.top_events) - 1:
            messagebox.showinfo("Move Down", "This event is already at the bottom.")
            return
        # Swap with the one below it.
        self.top_events[index], self.top_events[index + 1] = self.top_events[index + 1], self.top_events[index]
        self.update_views()

    def get_top_level_nodes(self):
        """Return a list of all nodes that have no parent."""
        all_nodes = self.get_all_nodes()
        top_level = [node for node in all_nodes if not node.parents]
        return top_level
        
    def find_node_by_id_all(self, unique_id):
        for top in self.top_events:
            result = self.find_node_by_id(top, unique_id)
            if result is not None:
                return result
        return None

    def edit_selected(self):
        sel = self.treeview.selection()
        target = None
        if sel:
            try:
                node_id = int(self.treeview.item(sel[0], "tags")[0])
            except (IndexError, ValueError):
                return
            target = self.find_node_by_id_all(node_id)
        elif self.selected_node:
            target = self.selected_node
        if not target:
            messagebox.showwarning("No selection", "Select a node to edit.")
            return

        # If the node is a clone, resolve it to its original.
        if not target.is_primary_instance and hasattr(target, "original") and target.original:
            target = target.original

        EditNodeDialog(self.root, target, self)
        self.update_views()

    def add_top_level_event(self):
        new_event = FaultTreeNode("", "TOP EVENT")
        new_event.x, new_event.y = 300, 200
        new_event.is_top_event = True
        self.top_events.append(new_event)
        self.root_node = new_event
        self.update_views()

    def edit_project_properties(self):
        prop_win = tk.Toplevel(self.root)
        prop_win.title("Project Properties")
        prop_win.geometry("400x200")
        dialog_font = tkFont.Font(family="Arial", size=10)

        ttk.Label(prop_win, text="PDF Report Name:", font=dialog_font).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        pdf_entry = tk.Entry(prop_win, width=40, font=dialog_font)
        pdf_entry.insert(0, self.project_properties.get("pdf_report_name", "Autonomous Driving Risk Assessment PDF Report"))
        pdf_entry.grid(row=0, column=1, padx=10, pady=10)

        # New checkbox to choose between detailed formulas or score results only.
        # Default to showing detailed formulas.
        var_detailed = tk.BooleanVar(value=self.project_properties.get("pdf_detailed_formulas", True))
        chk = tk.Checkbutton(prop_win, text="Show Detailed Formulas in PDF Report", variable=var_detailed, font=dialog_font)
        chk.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        def save_props():
            new_name = pdf_entry.get().strip()
            if new_name:
                self.project_properties["pdf_report_name"] = new_name
                self.project_properties["pdf_detailed_formulas"] = var_detailed.get()
                messagebox.showinfo("Project Properties", "Project properties updated.")
            else:
                messagebox.showwarning("Project Properties", "PDF Report Name cannot be empty.")
            prop_win.destroy()

        save_btn = tk.Button(prop_win, text="Save", command=save_props, font=dialog_font)
        save_btn.grid(row=2, column=0, columnspan=2, pady=10)
        prop_win.transient(self.root)
        prop_win.grab_set()
        self.root.wait_window(prop_win)

    def create_diagram_image(self):
        self.canvas.update()
        bbox = self.canvas.bbox("all")
        if not bbox:
            return None
        x, y, w, h = bbox[0], bbox[1], bbox[2]-bbox[0], bbox[3]-bbox[1]
        ps = self.canvas.postscript(colormode="color", x=x, y=y, width=w, height=h)
        from io import BytesIO
        ps_bytes = BytesIO(ps.encode("utf-8"))
        img = Image.open(ps_bytes)
        img.load(scale=3)
        return img.convert("RGB")

    def get_page_nodes(self, node):
        result = []
        if node.is_page and node != self.root_node:
            result.append(node)
        for child in node.children:
            result.extend(self.get_page_nodes(child))
        return result

    def capture_page_diagram(self, page_node):
        """
        Create an off-screen Toplevel with a Canvas, draw the page diagram (using PageDiagram),
        and return a PIL Image of the diagram.
        """
        from io import BytesIO
        from PIL import Image

        # Create a temporary Toplevel window and canvas
        temp = tk.Toplevel(self.root)
        temp.withdraw()
        canvas = tk.Canvas(temp, bg="white", width=2000, height=2000)
        canvas.pack()
        
        # Create and redraw the page diagram
        pd = PageDiagram(self, page_node, canvas)
        pd.redraw_canvas()
        
        # Remove grid if present and force an update
        canvas.delete("grid")
        canvas.update()
        
        # Get the bounding box; print debug info if empty.
        bbox = canvas.bbox("all")
        if not bbox:
            print(f"Debug: No drawing found for page node {page_node.unique_id} - bbox is empty.")
            temp.destroy()
            return None
        
        x, y, x2, y2 = bbox
        width, height = x2 - x, y2 - y
        print(f"Debug: Capturing page diagram for node {page_node.unique_id} with bbox=({x},{y},{x2},{y2})")
        
        # Get the PostScript output for the region.
        ps = canvas.postscript(colormode="color", x=x, y=y, width=width, height=height)
        ps_bytes = BytesIO(ps.encode("utf-8"))
        
        try:
            img = Image.open(ps_bytes)
            img.load(scale=3)
        except Exception as e:
            print(f"Debug: Error loading image for page node {page_node.unique_id}: {e}")
            img = None
        temp.destroy()
        return img.convert("RGB") if img else None

    def metric_to_text(self, metric_type, value):
        if value is None:
            return "unknown"
        disc = AD_RiskAssessment_Helper.discretize_level(value)
        if metric_type == "maturity":
            return "high maturity" if disc == 5 else "low maturity" if disc == 1 else f"a maturity of {disc}"
        elif metric_type == "rigor":
            return "high rigor" if disc == 5 else "low rigor" if disc == 1 else f"a rigor of {disc}"
        elif metric_type == "severity":
            return "high severity" if disc == 5 else "low severity" if disc == 1 else f"a severity of {disc}"
        else:
            return str(disc)

    def assurance_level_text(self, level):
        mapping = {1:"extra low",2:"low",3:"medium",4:"high",5:"high+"}
        return mapping.get(level, str(level))

    def calculate_cut_sets(self, node):
        if not node.children:
            return [{node.unique_id}]
        gate = (node.gate_type or "AND").upper() if node.node_type.upper() in ["TOP EVENT", "GATE", "RIGOR LEVEL"] else "AND"
        child_cut_sets = [self.calculate_cut_sets(child) for child in node.children]
        if gate == "OR":
            result = []
            for cuts in child_cut_sets:
                result.extend(cuts)
            return result
        elif gate == "AND":
            result = [set()]
            for cuts in child_cut_sets:
                temp = []
                for partial in result:
                    for cs in cuts:
                        temp.append(partial.union(cs))
                result = temp
            return result
        else:
            result = []
            for cuts in child_cut_sets:
                result.extend(cuts)
            return result

    def build_hierarchical_argumentation(self, node, indent=0):
        indent_str = "    " * indent
        node_name = node.user_name if node.user_name else f"Node {node.unique_id}"
        details = f"{node.node_type}"
        if node.input_subtype:
            details += f" ({node.input_subtype})"
        if node.description:
            details += f": {node.description}"
        metric_type = "maturity" if node.node_type.upper() in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"] else "rigor"
        metric_descr = self.metric_to_text(metric_type, node.quant_value)
        line = f"{indent_str}- {node_name} ({details}) -> {metric_descr}"
        if node.rationale and node.node_type.upper() not in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
            line += f" [Rationale: {node.rationale.strip()}]"
        child_lines = [self.build_hierarchical_argumentation(child, indent+1) for child in node.children]
        if child_lines:
            line += "\n" + "\n".join(child_lines)
        return line

    def build_hierarchical_argumentation_common(self, node, indent=0, described=None):
        if described is None:
            described = set()
        indent_str = "    " * indent
        node_name = node.user_name if node.user_name else f"Node {node.unique_id}"
        if node.unique_id not in described:
            details = f"{node.node_type}"
            if node.input_subtype:
                details += f" ({node.input_subtype})"
            if node.description:
                details += f": {node.description}"
            described.add(node.unique_id)
        else:
            details = f"{node.node_type} (see common cause: {node_name})"
        metric_type = "maturity" if node.node_type.upper() in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"] else "rigor"
        metric_descr = self.metric_to_text(metric_type, node.quant_value)
        line = f"{indent_str}- {node_name} ({details}) -> {metric_descr}"
        if node.rationale and node.node_type.upper() not in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
            line += f" [Rationale: {node.rationale.strip()}]"
        child_lines = [self.build_hierarchical_argumentation_common(child, indent+1, described) for child in node.children]
        if child_lines:
            line += "\n" + "\n".join(child_lines)
        return line

    def build_page_argumentation(self, page_node):
        return self.build_hierarchical_argumentation(page_node)

    def build_unified_recommendation_table(self):
        """
        Collect ALL nodes across ALL top-level events, group them by the
        recommendation(s) they trigger, and return a single LongTable.
        
        *Only primary nodes (originals) are used so that clones are not duplicated.
        Each node gets its own row, so large text can split across pages.
        """
        from reportlab.platypus import LongTable, Paragraph
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import TableStyle

        style_sheet = getSampleStyleSheet()
        body_style = style_sheet["BodyText"]
        header_style = ParagraphStyle(
            name="RecHeader",
            parent=body_style,
            fontSize=5,
            leading=6,
            wordWrap='CJK',
            alignment=1
        )

        # 1) Gather ALL nodes from ALL top events.
        # Assumes get_all_nodes_in_model() is defined to merge all nodes.
        all_nodes = self.get_all_nodes_in_model()
        if not all_nodes:
            print("Debug: No nodes found in the entire model.")
            return None

        # 2) Filter out clones: only include primary instances.
        primary_nodes = [n for n in all_nodes if n.is_primary_instance]

        # 3) Build a mapping: recommendation text -> list of nodes that trigger it.
        rec_to_nodes = {}
        for node in primary_nodes:
            # Only consider nodes with a quant_value and a nonempty description.
            if node.quant_value is not None and node.description:
                discrete = AD_RiskAssessment_Helper.discretize_level(node.quant_value)
                extra_dict = dynamic_recommendations.get(discrete, {}).get("Extra Recommendations", {})
                desc_lower = node.description.lower()
                for keyword, rec_text in extra_dict.items():
                    if keyword.lower() in desc_lower:
                        rec_to_nodes.setdefault(rec_text, []).append(node)

        if not rec_to_nodes:
            print("Debug: No matching recommendations found for any node.")
            return None

        # 4) Build the table rows.
        # We use two columns: "Extra Recommendation" and "Metric Details"
        # For each recommendation, the first row shows the recommendation text and the details
        # for the first node; subsequent rows leave the recommendation column blank.
        data = [[
            Paragraph("<b>Extra Recommendation</b>", header_style),
            Paragraph("<b>Metric Details</b>", header_style)
        ]]

        for rec_text, nodes in rec_to_nodes.items():
            first_row = True
            for node in nodes:
                # Use the node's display_label if it does not fall back to "Node ..."; otherwise, use the quant_value.
                metric_str = (node.display_label 
                              if node.display_label and not node.display_label.startswith("Node")
                              else (f"{node.quant_value:.2f}" if node.quant_value is not None else "N/A"))
                desc = (node.description or "N/A").strip().replace("\n", "<br/>")
                rat = (node.rationale or "N/A").strip().replace("\n", "<br/>")
                node_details = (
                    f"{node.unique_id}: {node.name}"
                    f"<br/><b>Metric:</b> {metric_str}"
                    f"<br/><b>Desc:</b> {desc}"
                    f"<br/><b>Rationale:</b> {rat}"
                )
                if first_row:
                    data.append([
                        Paragraph(rec_text, body_style),
                        Paragraph(node_details, body_style)
                    ])
                    first_row = False
                else:
                    data.append([
                        "",
                        Paragraph(node_details, body_style)
                    ])

        # 5) Create and style the LongTable.
        col_widths = [200, 450]
        table = LongTable(data, colWidths=col_widths, repeatRows=1, splitByRow=True)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.orange),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('FONTSIZE', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        return table

    def build_base_events_table_html(self,root_node):
        """
        Traverse the fault tree starting from root_node and collect all base events (leaf nodes).
        Return an HTML string representing a table with columns:
        Node ID, Name, Score, Description, and Rationale.
        
        The table header cells are styled with an orange background (#FFCC99),
        and multiline descriptions/rationales are preserved by converting newlines to <br>.
        """
        base_events = []
        
        # Collect all leaf nodes (base events).
        def traverse(n):
            if not n.children:
                base_events.append(n)
            else:
                for child in n.children:
                    traverse(child)
        traverse(root_node)
        
        # Build the HTML table.
        html_lines = []
        html_lines.append('<table style="border-collapse: collapse; width: 100%;">')
        
        # Table header row with orange background.
        html_lines.append(
            '  <thead>'
            '    <tr style="background-color: #FFCC99;">'
            '      <th style="border: 1px solid #ccc; padding: 8px;">Node ID</th>'
            '      <th style="border: 1px solid #ccc; padding: 8px;">Name</th>'
            '      <th style="border: 1px solid #ccc; padding: 8px;">Score</th>'
            '      <th style="border: 1px solid #ccc; padding: 8px;">Description</th>'
            '      <th style="border: 1px solid #ccc; padding: 8px;">Rationale</th>'
            '    </tr>'
            '  </thead>'
        )
        html_lines.append('  <tbody>')
        
        for node in base_events:
            node_id = str(node.unique_id)
            name = node.name or f"Node {node.unique_id}"
            score = f"{node.quant_value:.2f}" if node.quant_value is not None else "N/A"
            
            # Convert newlines to <br> for multiline display.
            desc = node.description.strip().replace('\n', '<br>') if node.description else "N/A"
            rat = node.rationale.strip().replace('\n', '<br>') if node.rationale else "N/A"
            
            row_html = (
                '    <tr>'
                f'      <td style="border: 1px solid #ccc; padding: 8px; vertical-align: top;">{node_id}</td>'
                f'      <td style="border: 1px solid #ccc; padding: 8px; vertical-align: top;">{name}</td>'
                f'      <td style="border: 1px solid #ccc; padding: 8px; vertical-align: top;">{score}</td>'
                f'      <td style="border: 1px solid #ccc; padding: 8px; vertical-align: top;">{desc}</td>'
                f'      <td style="border: 1px solid #ccc; padding: 8px; vertical-align: top;">{rat}</td>'
                '    </tr>'
            )
            html_lines.append(row_html)
        
        html_lines.append('  </tbody>')
        html_lines.append('</table>')
        
        return "\n".join(html_lines)

    def build_argumentation(self, node):
        if not node.children:
            return ""
        header = ""
        if node.node_type.upper() == "TOP EVENT":
            disc = AD_RiskAssessment_Helper.discretize_level(node.quant_value)
            assurance_descr = self.assurance_level_text(disc)
            severity_str = f"{node.severity}" if node.severity is not None else "N/A"
            controllability_str = f"{node.controllability}" if node.controllability is not None else "N/A"
            header += (
                f"Prototype Assurance Level (PAL) Explanation:<br/>"
                f"Based on the aggregated scores of its child nodes, this top event has been assigned an Prototype Assurance Level (PAL) of <b>{assurance_descr}</b> "
                f"with a severity rating of <b>{severity_str}</b> and controllability <b>{controllability_str}</b>.<br/><br/>"
            )
            # Append the dynamically generated recommendations.
            header += self.generate_recommendations_for_top_event(node) + "<br/>"
        # Now generate the cut-set table.
        nodes_by_id = {}
        def map_nodes(n):
            nodes_by_id[n.unique_id] = n
            for child in n.children:
                map_nodes(child)
        map_nodes(node)
        cut_sets = self.calculate_cut_sets(node)
        cut_set_table = "Cut Set Table:<br/>"
        for i, cs in enumerate(cut_sets, start=1):
            cs_ids = ", ".join(f"Node {uid}" for uid in sorted(cs))
            cut_set_table += f"Cut Set {i}: {cs_ids}<br/>"
        node_definitions = "Node Definitions:<br/>"
        unique_ids = set()
        for cs in cut_sets:
            unique_ids.update(cs)
        for uid in sorted(unique_ids):
            n = nodes_by_id.get(uid)
            if n is None:
                continue
            subtype = n.input_subtype if n.input_subtype is not None else (
                VALID_SUBTYPES["Confidence"][0] if n.node_type.upper() == "CONFIDENCE LEVEL"
                else VALID_SUBTYPES.get("Prototype Assurance Level (PAL)", ["Default"])[0]
            )
            desc = n.description.strip() if n.description else "No description provided."
            node_definitions += f"Node {uid}: {n.name}<br/>"
            node_definitions += f"Type: {n.node_type}, Subtype: {subtype}<br/>"
            node_definitions += f"Description: {desc}<br/><br/>"
        diagram_note = "Cause-and-Effect Diagram is generated below.<br/>"
        return header + cut_set_table + "<br/>" + node_definitions + "<br/>" + diagram_note
       
    def auto_create_argumentation(self, node, suppress_top_event_recommendations=False):
        """
        Generate qualitative argumentation text for a given node.
        For a TOP EVENT (unless suppressed), include dynamic recommendations from the dictionary
        filtered by the node’s description. For non–top-level nodes, simply display the node's input score,
        description, and rationale.
        """
        level = AD_RiskAssessment_Helper.discretize_level(node.quant_value) if node.quant_value is not None else 1

        if node.node_type.upper() == "TOP EVENT" and not suppress_top_event_recommendations:
            assurance_descr = self.assurance_level_text(level)
            severity_str = f"{node.severity}" if node.severity is not None else "N/A"
            controllability_str = f"{node.controllability}" if node.controllability is not None else "N/A"
            header = (
                f"Prototype Assurance Level (PAL) Explanation:\n"
                f"This top event is assigned an Prototype Assurance Level (PAL) of '{assurance_descr}' with a severity rating of {severity_str} and controllability {controllability_str}.\n\n"
            )
            # Instead of showing all dynamic recommendations, select only those triggered by the description.
            rec_from_desc = self.get_recommendation_from_description(node.description, level)
            if rec_from_desc:
                base_arg = header + "Dynamic Recommendation:\n" + rec_from_desc
            else:
                # If no keyword found, show the full recommendations.
                rec = dynamic_recommendations.get(level, {})
                rec_lines = []
                for category in ["Testing Requirements", "IFTD Responsibilities", "Preventive Maintenance Actions", "Relevant AVSC Guidelines"]:
                    if category in rec:
                        rec_lines.append(f"{category}: {rec[category]}")
                rec_text = "\n".join(rec_lines)
                base_arg = header + "Recommendations:\n" + rec_text
        elif node.node_type.upper() == "TOP EVENT" and suppress_top_event_recommendations:
            base_arg = f"Top Event: Input score: {node.quant_value:.2f}" if node.quant_value is not None else "Top Event: No input score provided."
        else:
            base_arg = f"Input score: {node.quant_value:.2f}" if node.quant_value is not None else "No input score provided."

        own_text = ""
        if node.description:
            own_text += f"Description: {node.description}\n"
        if node.rationale:
            own_text += f"Rationale: {node.rationale}\n"
        if not own_text:
            own_text = "No additional details provided."
            
        return base_arg + "\n\n" + own_text

    def generate_argumentation_report(self, event):
        """
        Generate dynamic assurance-level argumentation for a top-level event.
        In this version, the event’s description is added at the very beginning,
        followed by the Prototype Assurance Level (PAL) explanation (including the rationale behind its severity)
        and the dynamic recommendations.
        """
        # Ensure a quant_value exists; default to 1.
        quant = event.quant_value if event.quant_value is not None else 1
        level = AD_RiskAssessment_Helper.discretize_level(quant)
        assurance_level = self.assurance_level_text(level)
        severity = event.severity if event.severity is not None else "N/A"
        controllability = event.controllability if event.controllability is not None else "N/A"
        
        # Get dynamic recommendations from the dictionary.
        rec = dynamic_recommendations.get(level, {})
        test_req = rec.get("Testing Requirements", "N/A")
        iftd_resp = rec.get("IFTD Responsibilities", "N/A")
        maint_act = rec.get("Preventive Maintenance Actions", "N/A")
        avsc_guid = rec.get("Relevant AVSC Guidelines", "N/A")
        
        # Get and clean up the top event’s description and rationale.
        top_description = event.description.strip() if event.description and event.description.strip() else "N/A"
        top_rationale = event.rationale.strip() if event.rationale and event.rationale.strip() else "N/A"
        
        text = (
            f"Description:<br/>{top_description}<br/><br/>"
            f"Prototype Assurance Level (PAL) Explanation:<br/>"
            f"This top event is assigned an Prototype Assurance Level (PAL) of <b>{assurance_level}</b> "
            f"with a severity rating of <b>{severity}</b> and controllability <b>{controllability}</b>.<br/>"
            f"Rationale for Severity: {top_rationale}<br/><br/>"
            #"Dynamic Recommendations:<br/>"
            #f"<b>Testing Requirements:</b> {test_req}<br/>"
            #f"<b>IFTD Responsibilities:</b> {iftd_resp}<br/>"
            #f"<b>Preventive Maintenance Actions:</b> {maint_act}<br/>"
            #f"<b>Relevant AVSC Guidelines:</b> {avsc_guid}<br/>"
        )
        return text

    def get_extra_recommendations_list(self, description, level):
        """
        Given a node's description and its Prototype Assurance Level (PAL), return a list of extra recommendations.
        This function iterates over all keys in the level's "Extra Recommendations" dictionary and
        collects the recommendation text for every keyword found in the description.
        """
        if not description:
            return []
        desc = description.lower()
        level_extras = dynamic_recommendations.get(level, {}).get("Extra Recommendations", {})
        rec_list = []
        for keyword, rec in level_extras.items():
            if keyword.lower() in desc:
                rec_list.append(rec)
        return rec_list

    def get_extra_recommendations_from_level(self,description, level):
        """
        Given a node's description and its Prototype Assurance Level (PAL) (1-5), look up keywords from the level's 
        "Extra Recommendations" in the dynamic_recommendations dictionary. If any keyword is found in the description
        (within a proximity of malfunction words), return the extra recommendations.
        """
        if not description:
            return ""
        desc = description.lower()
        level_extras = dynamic_recommendations.get(level, {}).get("Extra Recommendations", {})
        malfunction_words = ["unintended", "no", "not", "excessive", "incorrect"]
        
        recommendations = []
        for keyword, rec in level_extras.items():
            # Check if the keyword is present.
            if re.search(r'\b' + re.escape(keyword) + r'\b', desc):
                # Look for a malfunction word within 5 words of the keyword.
                pattern = r'\b' + re.escape(keyword) + r'\b(?:\W+\w+){0,5}\W+(?:' + "|".join(malfunction_words) + r')\b'
                if re.search(pattern, desc):
                    recommendations.append(rec)
        if recommendations:
            return "\nExtra Testing Recommendations:\n" + "\n".join(f"- {r}" for r in recommendations)
        return ""

    def get_recommendation_from_description(self, description, level):
        """
        Given a node's description and its Prototype Assurance Level (PAL), this function iterates over all keys 
        in the corresponding level's "Extra Recommendations" dictionary. It checks if each keyword 
        appears in the description (in a case-insensitive manner) and concatenates all matching recommendations.
        """
        if not description:
            return ""
        desc = description.lower()
        level_extras = dynamic_recommendations.get(level, {}).get("Extra Recommendations", {})
        rec_list = []
        for keyword, rec in level_extras.items():
            if keyword.lower() in desc:
                rec_list.append(rec)
        return " ".join(rec_list)
    
    def analyze_common_causes(self, node):
        occurrence = {}
        def traverse(n):
            if n.unique_id in occurrence:
                occurrence[n.unique_id]["count"] += 1
            else:
                occurrence[n.unique_id] = {"node": n, "count": 1}
            for child in n.children:
                traverse(child)
        traverse(node)
        report_lines = ["Common Cause Analysis:"]
        for uid, info in occurrence.items():
            if info["count"] > 1:
                n = info["node"]
                name = n.user_name if n.user_name else f"Node {n.unique_id}"
                report_lines.append(f" - {name} (Type: {n.node_type}) appears {info['count']} times. Description: {n.description or 'No description'}")
        if len(report_lines) == 1:
            report_lines.append(" None found.")
        return "\n".join(report_lines)

    def build_text_report(self, node, indent=0):
        report = "    " * indent + f"{node.name} ({node.node_type}"
        if node.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
            report += f", {node.gate_type}"
        report += ")"
        if node.display_label:
            report += f" => {node.display_label}"
        arg_text = self.build_argumentation(node)
        if arg_text:
            report += f"\n{'    ' * (indent+1)}Argumentation: {arg_text}"
        report += "\n\n"
        for child in node.children:
            report += self.build_text_report(child, indent+1)
        return report

    def all_children_are_base_events(self,node):
        """
        Return True if *every* child of 'node' is a base event 
        (i.e. Confidence Level or Robustness Score).
        """
        # If node has no children, we treat it as "False" (it’s effectively a leaf, not a gate).
        if not node.children:
            return False

        for child in node.children:
            t = child.node_type.upper()
            if t not in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
                return False
        return True

    def build_simplified_fta_model(self, top_event):
        """
        Build a simplified FTA model from the fault tree by including only the gate-level nodes.
        If a node is a GATE, RIGOR LEVEL, or TOP EVENT but all its children are base events,
        we will skip showing its gate_type.
        """
        nodes = []
        edges = []
        
        def traverse(node):
            node_type_up = node.node_type.upper()
            if node_type_up in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
                final_gate_type = node.gate_type  # e.g. "AND" or "OR"

                node_info = {
                    "id": str(node.unique_id),
                    "label": node.name,
                    "gate_type": final_gate_type,   # store it only if not all children are base
                }
                if node.input_subtype:
                    node_info["subtype"] = node.input_subtype
                
                nodes.append(node_info)

                # Only traverse children that are also gates or top events
                for child in node.children:
                    child_type = child.node_type.upper()
                    if child_type in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
                        edges.append({"source": str(node.unique_id), "target": str(child.unique_id)})
                        traverse(child)

        traverse(top_event)
        return {"nodes": nodes, "edges": edges}

    @staticmethod
    def auto_generate_fta_diagram(fta_model, output_path):
        """
        Generate a cause-and-effect diagram with a layered (hierarchical) layout,
        but draw the arrows in reverse (child -> parent).
        """
        import networkx as nx
        import matplotlib.pyplot as plt
        try:
            from adjustText import adjust_text
        except ImportError:
            adjust_text = None
        import numpy as np

        # --- 1) Build the directed graph (parent->child) ---
        G = nx.DiGraph()
        node_labels = {}
        node_colors = {}

        for node in fta_model["nodes"]:
            node_id = node["id"]
            label   = node.get("label", f"Node {node_id}")

            # If there's a gate_type, append it to the label
            gate_type = node.get("gate_type", "")
            if gate_type:
                # e.g. label = "Node 1\n(AND)"
                label += f"\n({gate_type.upper()})"

            G.add_node(node_id)
            node_labels[node_id] = label

            # Keep your color logic based on "subtype":
            subtype = node.get("subtype", "").lower()
            if "vehicle level function" in subtype:
                node_colors[node_id] = "lightcoral"
            elif "safety mechanism" in subtype:
                node_colors[node_id] = "lightyellow"
            elif "capability" in subtype:
                node_colors[node_id] = "lightblue"
            else:
                node_colors[node_id] = "white"  # clone

        # Add edges
        for edge in fta_model["edges"]:
            src = edge["source"]
            tgt = edge["target"]
            if not G.has_node(src) or not G.has_node(tgt):
                continue
            G.add_edge(src, tgt)

        # --- 2) Identify the top event as 'root' (layer 0) ---
        if fta_model["nodes"]:
            top_event_id = fta_model["nodes"][0]["id"]
        else:
            # If empty, just bail out
            plt.figure(figsize=(8,6))
            plt.title("No nodes to display")
            plt.savefig(output_path)
            plt.close()
            return

        # --- 3) BFS layering from top_event to find each node's layer ---
        layers = {}
        layers[top_event_id] = 0
        queue = [top_event_id]
        visited = set([top_event_id])

        while queue:
            current = queue.pop(0)
            current_layer = layers[current]
            for child in G.successors(current):
                if child not in visited:
                    visited.add(child)
                    layers[child] = current_layer + 1
                    queue.append(child)

        # Any node not reached gets placed in a higher layer
        max_layer = max(layers.values()) if layers else 0
        for n in G.nodes():
            if n not in layers:
                max_layer += 1
                layers[n] = max_layer

        # Group nodes by layer
        layer_dict = {}
        for node_id, layer in layers.items():
            layer_dict.setdefault(layer, []).append(node_id)

        # --- 4) Assign (x, y) by layer ---
        horizontal_gap = 2.0
        vertical_gap   = 1.0
        pos = {}

        for layer in sorted(layer_dict.keys()):
            node_list = layer_dict[layer]

            # Sort siblings by average parent index (optional)
            def avg_parent_position(n):
                parents = list(G.predecessors(n))
                if not parents:
                    return 0
                # we assume all parents are in a smaller layer
                return sum(layer_dict[layers[p]].index(p) for p in parents) / len(parents)

            node_list.sort(key=avg_parent_position)

            # Place them at x = layer*gap, y around 0
            middle = (len(node_list) - 1) / 2.0
            for i, n in enumerate(node_list):
                x = layer * horizontal_gap
                y = (i - middle) * vertical_gap
                pos[n] = (x, y)

        # --- 5) Light collision-avoidance pass (optional) ---
        def get_node_bbox(p, box_size=0.3):
            return (p[0] - box_size, p[1] - box_size, p[0] + box_size, p[1] + box_size)

        def bboxes_overlap(b1, b2):
            return not (b1[2] < b2[0] or b1[0] > b2[2] or b1[3] < b2[1] or b1[1] > b2[3])

        for _ in range(10):
            for n1 in G.nodes():
                for n2 in G.nodes():
                    if n1 == n2:
                        continue
                    b1 = get_node_bbox(pos[n1])
                    b2 = get_node_bbox(pos[n2])
                    if bboxes_overlap(b1, b2):
                        p1 = np.array(pos[n1])
                        p2 = np.array(pos[n2])
                        delta = p1 - p2
                        dist = np.linalg.norm(delta) + 1e-9
                        push = 0.02
                        shift = (delta/dist)*push
                        pos[n1] = tuple(p1 + shift)
                        pos[n2] = tuple(p2 - shift)

        # --- 6) Draw the diagram with REVERSED edges (child->parent) ---
        plt.figure(figsize=(12,8))

        # Build reversed edge list for drawing:
        reversed_edges = [(t, s) for (s, t) in G.edges()]

        nx.draw_networkx_edges(
            G, pos,
            edgelist=reversed_edges,    # <--- Inverted direction
            arrowstyle='-|>',
            arrowsize=20,
            edge_color='gray',
            connectionstyle="arc3,rad=0.0",
            min_source_margin=15,
            min_target_margin=15
        )

        # Keep your node colors from node_colors
        node_color_list = [node_colors[n] for n in G.nodes()]
        nx.draw_networkx_nodes(G, pos,
                               node_color=node_color_list,
                               node_size=1200,
                               edgecolors="black")

        # Draw labels
        text_items = []
        for n, (x, y) in pos.items():
            lbl = node_labels.get(n, str(n))
            txt = plt.text(x, y, lbl, fontsize=9, ha='center', va='center', wrap=True)
            text_items.append(txt)

        # Optionally adjust text to avoid overlap
        if adjust_text:
            adjust_text(text_items, arrowprops=dict(arrowstyle="-", color="gray"))

        plt.title("Cause and Effect Diagram")
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()

    def build_dynamic_recommendations_table(events, app):
        """
        (Optional) If you still want to have a compact table of per-event recommendations,
        this function builds a multiline LongTable with columns:
        [Event Name, Prototype Assurance Level (PAL), Severity, Controllability, Description, Rationale, Dynamic Recommendations].
        (Not used in the final report if you prefer only the consolidated argumentation.)
        """
        style_sheet = getSampleStyleSheet()
        header_style = ParagraphStyle(
            name="CompactHeader",
            parent=style_sheet["BodyText"],
            fontSize=4,
            leading=5,
            wordWrap='CJK',
            alignment=1
        )
        body_style = ParagraphStyle(
            name="CompactBody",
            parent=style_sheet["BodyText"],
            fontSize=5,
            leading=6,
            wordWrap='CJK'
        )
        
        data = [[
            Paragraph("<b>Event Name</b>", header_style),
            Paragraph("<b>Prototype Assurance Level (PAL)</b>", header_style),
            Paragraph("<b>Severity</b>", header_style),
            Paragraph("<b>Controllability</b>", header_style),
            Paragraph("<b>Description</b>", header_style),
            Paragraph("<b>Rationale</b>", header_style),
            Paragraph("<b>Recommendations</b>", header_style),
        ]]
        
        for event in events:
            event_name = event.name if event.name else f"Node {event.unique_id}"
            if event.quant_value is not None:
                disc_level = AD_RiskAssessment_Helper.discretize_level(event.quant_value)
                assurance_str = app.assurance_level_text(disc_level)
            else:
                assurance_str = "N/A"
            severity_str = str(event.severity) if event.severity is not None else "N/A"
            controllability_str = str(event.controllability) if event.controllability is not None else "N/A"
            desc_text = (event.description or "N/A").strip().replace("\n", "<br/>")
            rat_text = (event.rationale or "N/A").strip().replace("\n", "<br/>")
            rec_text = app.generate_argumentation_report(event)
            if isinstance(rec_text, list):
                rec_text = "\n".join(str(x) for x in rec_text)
            rec_text = rec_text.strip().replace("\n", "<br/>")
            data.append([
                Paragraph(event_name, body_style),
                Paragraph(assurance_str, body_style),
                Paragraph(severity_str, body_style),
                Paragraph(controllability_str, body_style),
                Paragraph(desc_text, body_style),
                Paragraph(rat_text, body_style),
                Paragraph(rec_text, body_style),
            ])
        
        col_widths = [100, 60, 40, 40, 150, 150, 200]
        table = LongTable(data, colWidths=col_widths, repeatRows=1, splitByRow=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.orange),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ROWHEIGHT', (0,0), (-1,0), 12),
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('FONTSIZE', (0,1), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 1),
            ('RIGHTPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('SPLITTABLE', (0,0), (-1,-1), True),
        ]))
        return table

    def get_all_nodes_no_filter(self,node):
        nodes = [node]
        for child in node.children:
            nodes.extend(self.get_all_nodes_no_filter(child))
        return nodes
        
    def derive_requirements_for_event(self, event):
        req_set = set()
        for node in self.get_all_nodes(event):
            if hasattr(node, "safety_requirements"):
                for req in node.safety_requirements:
                    req_set.add(f"[{req['id']}] [{req['req_type']}] {req['text']}")
        return req_set

    def get_combined_safety_requirements(self,node):
        """
        Returns a list of safety requirement dicts for the given node.
        If the node is a clone, it also combines the original node's safety_requirements.
        """
        req_list = []
        # Always take the node's own requirements if they exist.
        if hasattr(node, "safety_requirements") and node.safety_requirements:
            req_list.extend(node.safety_requirements)
        # If node is a clone, also add requirements from its original.
        if not node.is_primary_instance and hasattr(node, "original") and node.original.safety_requirements:
            req_list.extend(node.original.safety_requirements)
        return req_list

    def get_top_event(self, node):
        """
        Walk up the parent chain until a node whose node_type is 'TOP EVENT' is found.
        If none is found, return the node itself.
        """
        current = node
        while current.parents:
            for parent in current.parents:
                if parent.node_type.upper() == "TOP EVENT":
                    print(f"DEBUG: Found TOP EVENT for node {node.unique_id}: {parent.name}")
                    return parent
            current = current.parents[0]
        print(f"DEBUG: No TOP EVENT found for node {node.unique_id}; returning self")
        return node

    def aggregate_safety_requirements(self, node, all_nodes):
        aggregated = set()
        # Always add the node’s own safety requirements.
        for req in node.get("safety_requirements", []):
            aggregated.add(req["id"])
        
        # If this node is a clone, also add the original’s aggregated safety requirements.
        if node.get("original_id"):
            original = all_nodes.get(node["original_id"])
            if original:
                aggregated.update(self.aggregate_safety_requirements(original, all_nodes))
        
        # NEW: Also add safety requirements from the node’s immediate parents.
        for parent in node.get("parents", []):
            for req in parent.get("safety_requirements", []):
                aggregated.add(req["id"])
        
        # Recurse into children.
        for child in node.get("children", []):
            aggregated.update(self.aggregate_safety_requirements(child, all_nodes))
        
        node["aggregated_safety_requirements"] = sorted(aggregated)
        return aggregated

    def generate_top_event_summary(self, top_event):
        """
        Generates a structured, easy-to-read summary for a top-level event.
        
        It recursively collects all base nodes (nodes with type "CONFIDENCE LEVEL" or "ROBUSTNESS SCORE")
        from the event’s entire subtree (using originals for clones) and then constructs a multi-line summary
        that includes:
          - The top-level event name.
          - The required Prototype Assurance Level (PAL) (with numeric score) and the severity rating.
          - A bullet-point list of base nodes with their scores and rationales.
        """
        # Retrieve all nodes from the entire subtree (including originals for clones)
        all_nodes = self.get_all_nodes_no_filter(top_event)
        
        # Filter base nodes (confidence or robustness)
        base_nodes = [n for n in all_nodes if n.node_type.upper() in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]]
        
        # Build a bullet list for base nodes
        bullet_lines = []
        for bn in base_nodes:
            # Use the original's details for clones
            orig = bn if bn.is_primary_instance else bn.original
            identifier = orig.name if orig.name else f"Node {orig.unique_id}"
            score = f"{orig.quant_value:.2f}" if orig.quant_value is not None else "N/A"
            rationale = orig.rationale.strip() if orig.rationale and orig.rationale.strip() != "" else "No rationale provided"
            bullet_lines.append(f"• {identifier}: Score = {score}, Rationale: {rationale}")
        base_summary = "\n".join(bullet_lines) if bullet_lines else "No base nodes available."
        
        # Map overall assurance value to a descriptive level
        overall_assurance = top_event.quant_value if top_event.quant_value is not None else 1.0
        if overall_assurance >= 4.5:
            assurance_descr = "High+"
        elif overall_assurance >= 3.5:
            assurance_descr = "High"
        elif overall_assurance >= 2.5:
            assurance_descr = "Moderate"
        elif overall_assurance >= 1.5:
            assurance_descr = "Low"
        else:
            assurance_descr = "Very Low"
        
        # Use the top event's severity and controllability (defaults if missing)
        try:
            overall_severity = float(top_event.severity) if top_event.severity is not None else 5.0
        except Exception:
            overall_severity = 5.0
        try:
            overall_cont = float(top_event.controllability) if top_event.controllability is not None else 3.0
        except Exception:
            overall_cont = 3.0
        
        # Build the structured summary sentence
        summary_sentence = (
            f"Top-Level Event: {top_event.name}\n\n"
            f"Assurance Requirement:\n"
            f"  - Required Prototype Assurance Level (PAL): {assurance_descr} (Score: {overall_assurance:.2f})\n"
            f"  - Severity Rating: {overall_severity:.2f}\n"
            f"  - Controllability: {overall_cont:.2f}\n\n"
            f"Rationale:\n"
            f"  Based on analysis of its base nodes, the following factors contributed to this level:\n"
            f"{base_summary}"
        )
        return summary_sentence

    def _generate_pdf_report(self, include_assurance=True):
        report_title = self.project_properties.get("pdf_report_name", "Autonomous Driving Risk Assessment PDF Report")
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not path:
            return

        try:
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                Paragraph,
                Spacer,
                PageBreak,
                SimpleDocTemplate,
                Image as RLImage,
                Table,
                TableStyle,
            )
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from io import BytesIO
            import PIL.Image as PILImage
        except ImportError:
            messagebox.showerror(
                "Report",
                "Reportlab package is required to generate PDF reports. "
                "Please install it and try again.",
            )
            return

        # Build a dictionary of all nodes (using each node’s to_dict())
        all_nodes = {}
        for node in self.get_all_nodes_in_model():
            node_dict = node.to_dict()
            all_nodes[node.unique_id] = node_dict

        # Now, for each node in the model, aggregate its safety requirements recursively.
        for node_dict in all_nodes.values():
            self.aggregate_safety_requirements(node_dict, all_nodes)

        # Define document with extra margins.
        doc = SimpleDocTemplate(
            path,
            pagesize=landscape(letter),
            leftMargin=0.8 * inch,
            rightMargin=0.8 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch
        )

        pdf_styles = getSampleStyleSheet()
        preformatted_style = ParagraphStyle(name="Preformatted", fontName="Courier", fontSize=10)
        pdf_styles.add(preformatted_style)
        Story = []

        # -------------------------------------------------------------
        # Executive Summary Page (First Page)
        # -------------------------------------------------------------
        Story.append(Paragraph(report_title, pdf_styles["Title"]))
        Story.append(Spacer(1, 12))

        if include_assurance:
            exec_summary_text = (
            "<b>Executive Summary: Manual Calculation of Prototype Assurance Level (PAL)</b><br/><br/>"
                "This document provides a step-by-step procedure to manually calculate the Prototype Assurance Level (PAL) for a subsystem in an "
                "autonomous system. The Prototype Assurance Level (PAL) is a single metric ranging from 1 to 5 (mapped to qualitative labels: "
                "Extra Low, Low, Moderate, High, High+). Follow these instructions using the provided tables.<br/><br/>"
                
                "<b>Calculation Instructions:</b><br/>"
                "1. <u>Base Assurance Derivation</u>:<br/>"
                " a. Assign a Confidence Level (CL) and a Robustness Score (RS) to the component, each on a scale from 1 (Extra Low) to 5 (High+).<br/>"
                " b. Using Table 1 (Base Assurance Inversion Matrix), locate the cell at the intersection of the CL (row) and RS (column).<br/>"
                "  For example, a CL of 1 and an RS of 1 yields a base assurance value of 5, indicating a very high requirement for additional safety measures.<br/><br/>"
                "2. <u>Combining Multiple Components</u>:<br/>"
                " a. If the subsystem consists of multiple components, first compute the base assurance value for each component individually as described above.<br/>"
                " b. Then, combine these values based on how the components interact:<br/>"
                "  - If the components must all perform reliably (an AND configuration), use a complement-product method as outlined in Table 3 (AND Decomposition Guidelines).<br/>"
                "  - If the components function as alternative options (an OR configuration), simply compute the average of their assurance values (see Table 4 for OR Decomposition Guidelines).<br/>"
                " c. When both types of inputs are present, average the base-derived values with the aggregated values to obtain a combined score.<br/><br/>"
                "3. <u>Severity Adjustment</u>:<br/>"
                " a. Adjust the combined assurance value to reflect hazard severity.<br/>"
                " b. For most subsystems, take the highest severity rating from the related elements and compute the average with the combined assurance score.<br/>"
                " c. For vehicle-level functions, use the formula: <br/>"
                "  Final Assurance = (Combined Value + Severity) / 2 <br/>"
                " Ensure the final score remains within the 1 to 5 range.<br/><br/>"
                "4. <u>Final Discretization</u>:<br/>"
                " a. Round the adjusted assurance value to the nearest 0.5.<br/>"
                " b. Refer to Table 2 (Output Discretization Mapping) to map the rounded value to one of the five discrete Prototype Assurance Levels (PAL), "
                "which correspond to the qualitative labels (Extra Low, Low, Moderate, High, High+).<br/><br/>"
                "By following these steps—deriving a base assurance from individual Confidence and Robustness ratings, combining multiple values "
                "through averaging or using complement-product methods (depending on the configuration), adjusting for hazard severity, and finally "
                "discretizing the result—you can manually calculate the Prototype Assurance Level (PAL) for any subsystem in a clear and systematic manner."
            )
            Story.append(Paragraph(exec_summary_text, pdf_styles["Normal"]))
            Story.append(Spacer(1, 12))
            
            # --- Table 1: Base Assurance Inversion Matrix ---
            header_style = ParagraphStyle(name="SafetyGoalsHeader", parent=pdf_styles["Normal"], fontSize=10, leading=12, alignment=1)
            base_matrix_data = [
                [Paragraph("<b>Robustness \\ Confidence</b>", header_style),
                 Paragraph("<b>1 (Extra Low)</b>", header_style),
                 Paragraph("<b>2 (Low)</b>", header_style),
                 Paragraph("<b>3 (Moderate)</b>", header_style),
                 Paragraph("<b>4 (High)</b>", header_style),
                 Paragraph("<b>5 (High+)</b>", header_style)],
                [Paragraph("<b>1 (Extra Low)</b>", header_style),
                 Paragraph("High+", pdf_styles["Normal"]),
                 Paragraph("High+", pdf_styles["Normal"]),
                 Paragraph("High", pdf_styles["Normal"]),
                 Paragraph("High", pdf_styles["Normal"]),
                 Paragraph("High", pdf_styles["Normal"])],
                [Paragraph("<b>2 (Low)</b>", header_style),
                 Paragraph("High+", pdf_styles["Normal"]),
                 Paragraph("High+", pdf_styles["Normal"]),
                 Paragraph("High", pdf_styles["Normal"]),
                 Paragraph("Moderate", pdf_styles["Normal"]),
                 Paragraph("Moderate", pdf_styles["Normal"])],
                [Paragraph("<b>3 (Moderate)</b>", header_style),
                 Paragraph("High", pdf_styles["Normal"]),
                 Paragraph("High", pdf_styles["Normal"]),
                 Paragraph("Moderate", pdf_styles["Normal"]),
                 Paragraph("Moderate", pdf_styles["Normal"]),
                 Paragraph("Extra Low", pdf_styles["Normal"])],
                [Paragraph("<b>4 (High)</b>", header_style),
                 Paragraph("High", pdf_styles["Normal"]),
                 Paragraph("Moderate", pdf_styles["Normal"]),
                 Paragraph("Moderate", pdf_styles["Normal"]),
                 Paragraph("Extra Low", pdf_styles["Normal"]),
                 Paragraph("Extra Low", pdf_styles["Normal"])],
                [Paragraph("<b>5 (High+)</b>", header_style),
                 Paragraph("High", pdf_styles["Normal"]),
                 Paragraph("Moderate", pdf_styles["Normal"]),
                 Paragraph("Extra Low", pdf_styles["Normal"]),
                 Paragraph("Extra Low", pdf_styles["Normal"]),
                 Paragraph("Extra Low", pdf_styles["Normal"])]
            ]
            base_matrix_table = Table(base_matrix_data, colWidths=[80, 70, 70, 70, 70, 70])
            base_matrix_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                ('BACKGROUND', (0,0), (0,-1), colors.lightblue),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTSIZE', (0,0), (-1,-1), 8)
            ]))
            Story.append(Paragraph("Table 1: Base Assurance Inversion Matrix", pdf_styles["Heading3"]))
            Story.append(Spacer(1, 6))
            Story.append(base_matrix_table)
            Story.append(Spacer(1, 12))
            
            # --- Table 2: Output Discretization Mapping ---
            discretization_data = [
                [Paragraph("<b>Continuous Value (Rounded)</b>", header_style),
                 Paragraph("<b>Prototype Assurance Level (PAL)</b>", header_style)],
                [Paragraph("< 1.5", header_style), Paragraph("Level 1 (Extra Low)", pdf_styles["Normal"])],
                [Paragraph("1.5 – < 2.5", header_style), Paragraph("Level 2 (Low)", pdf_styles["Normal"])],
                [Paragraph("2.5 – < 3.5", header_style), Paragraph("Level 3 (Moderate)", pdf_styles["Normal"])],
                [Paragraph("3.5 – < 4.5", header_style), Paragraph("Level 4 (High)", pdf_styles["Normal"])],
                [Paragraph("≥ 4.5", header_style), Paragraph("Level 5 (High+)", pdf_styles["Normal"])]
            ]
            discretization_table = Table(discretization_data, colWidths=[150, 200])
            discretization_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTSIZE', (0,0), (-1,-1), 8)
            ]))
            Story.append(Paragraph("Table 2: Output Discretization Mapping", pdf_styles["Heading3"]))
            Story.append(Spacer(1, 6))
            Story.append(discretization_table)
            Story.append(Spacer(1, 12))
            
            # Define mapping from numeric level to qualitative label.
            level_labels = {1: "Extra Low", 2: "Low", 3: "Moderate", 4: "High", 5: "High+"}
    
            # ------------------------------------------------------------------
            # Helper: Get the highest Prototype Assurance Level (PAL) from immediate parents.
            # For a given node (or its clone), this returns the maximum assurance (as an integer 1-5)
            # among all its immediate parents. If no parent exists, it returns the node's own assurance.
            def get_immediate_parent_assurance(node):
                if node.parents:
                    assurances = []
                    for p in node.parents:
                        # For clones, use the original parent's assurance value.
                        parent = p if p.is_primary_instance else p.original
                        try:
                            val = int(parent.quant_value)
                        except (TypeError, ValueError):
                            val = 1
                        assurances.append(val)
                    return max(assurances) if assurances else int(node.quant_value if node.quant_value is not None else 1)
                else:
                    return int(node.quant_value if node.quant_value is not None else 1)
            # ------------------------------------------------------------------
    
            # --- Safety Goals Summary Table ---
            safety_goals_data = []
            header_style = ParagraphStyle(name="SafetyGoalsHeader", parent=pdf_styles["Normal"], fontSize=10, leading=12, alignment=1)
            safety_goals_data.append([
                Paragraph("<b>Safety Goal</b>", header_style),
                Paragraph("<b>Highest Immediate Parent Assurance</b>", header_style),
                Paragraph("<b>Linked Recommendations</b>", header_style)
            ])
                    
            # Instead of iterating over only top-level events,
            # we iterate over all nodes that have safety requirements.
            grouped_by_linked = {}
            for node in self.get_all_nodes_in_model():
                if hasattr(node, "safety_requirements") and node.safety_requirements:
                    # Determine the safety goal from the node.
                    safety_goal = node.safety_goal_description.strip() if node.safety_goal_description.strip() != "" else node.name
                    # Get the highest assurance from its immediate parent(s)
                    parent_assur = get_immediate_parent_assurance(node)
                    assurance_str = f"Level {parent_assur} ({level_labels.get(parent_assur, 'N/A')})"
                    # Use the node's description to generate a linked recommendation.
                    # (You can adjust this method as needed.)
                    linked_rec = self.generate_recommendations_for_top_event(node)
                    extra_recs = self.get_extra_recommendations_list(node.description,
                                                                      AD_RiskAssessment_Helper.discretize_level(node.quant_value))
                    if not extra_recs:
                        extra_recs = ["No Extra Recommendation"]
                    # Group by the linked recommendation text.
                    grouped_by_linked.setdefault(linked_rec, {})
                    for extra in extra_recs:
                        grouped_by_linked[linked_rec].setdefault(extra, [])
                        grouped_by_linked[linked_rec][extra].append(f"- {safety_goal} (Assurance: {assurance_str})")
    
            sg_data = []
            sg_data.append([
                Paragraph("<b>Linked Recommendation</b>", header_style),
                Paragraph("<b>Safety Goals Grouped by Extra Recommendation</b>", header_style)
            ])
            for linked_rec, extra_groups in grouped_by_linked.items():
                nested_text = ""
                for extra_rec, goals in extra_groups.items():
                    nested_text += f"<b>{extra_rec}:</b><br/>" + "<br/>".join(goals) + "<br/><br/>"
                sg_data.append([
                    Paragraph(linked_rec, pdf_styles["Normal"]),
                    Paragraph(nested_text, pdf_styles["Normal"])
                ])
            if len(sg_data) > 1:
                sg_table = Table(sg_data, colWidths=[200, 400])
                sg_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('FONTSIZE', (0,0), (-1,-1), 10),
                    ('ALIGN', (0,0), (-1,0), 'CENTER')
                ]))
                Story.append(Paragraph("Safety Goals Summary:", pdf_styles["Heading2"]))
                Story.append(Spacer(1, 12))
                Story.append(sg_table)
                Story.append(Spacer(1, 12))
            Story.append(PageBreak())
            
        # --- Per-Top-Level-Event Content (Diagrams and Argumentation) ---
        def scale_image(pil_img):
            """Scale images so they fit within the doc page nicely."""
            orig_width, orig_height = pil_img.size
            scale_factor = 0.95 * min(doc.width / orig_width, doc.height / orig_height, 1)
            desired_width = orig_width * scale_factor
            desired_height = orig_height * scale_factor
            return desired_width, desired_height

        processed_ids = set()
        for idx, event in enumerate(self.top_events, start=1):
            if event.unique_id in processed_ids:
                continue
            processed_ids.add(event.unique_id)
            
            Story.append(Paragraph(f"Top-Level Event #{idx}: {event.name}", pdf_styles["Heading2"]))
            Story.append(Spacer(1, 12))
            
            # Argumentation text
            argumentation_text = self.generate_argumentation_report(event)
            if isinstance(argumentation_text, list):
                argumentation_text = "\n".join(str(x) for x in argumentation_text)
            argumentation_text = argumentation_text.replace("\n", "<br/>")
            Story.append(Paragraph(argumentation_text, preformatted_style))
            Story.append(Spacer(1, 12))

            # (A) "Detailed" event diagram (the subtree as captured in code)
            event_img = self.capture_event_diagram(event)
            if event_img is not None:
                buf = BytesIO()
                event_img.save(buf, format="PNG")
                buf.seek(0)
                desired_width, desired_height = scale_image(event_img)
                rl_img = RLImage(buf, width=desired_width, height=desired_height)
                Story.append(Paragraph("Detailed Diagram (Subtree):", pdf_styles["Heading3"]))
                Story.append(Spacer(1, 12))
                Story.append(rl_img)
                Story.append(Spacer(1, 12))

            # (B) "Cause and Effect" BFS diagram: build a single-root model for THIS event only
            fta_model = self.build_simplified_fta_model(event)
            temp_diagram_path = f"temp_fta_diagram_{idx}.png"
            self.auto_generate_fta_diagram(fta_model, temp_diagram_path)
            try:
                with open(temp_diagram_path, "rb") as img_file:
                    buf = BytesIO(img_file.read())
                pil_img = PILImage.open(buf)
                desired_width, desired_height = scale_image(pil_img)
                buf.seek(0)
                rl_img2 = RLImage(buf, width=desired_width, height=desired_height)
                Story.append(Paragraph("Cause and Effect Diagram (Single Root):", pdf_styles["Heading3"]))
                Story.append(Spacer(1, 12))
                Story.append(rl_img2)
                Story.append(Spacer(1, 12))
            except Exception as e:
                Story.append(Paragraph(f"Error generating BFS diagram for {event.name}: {e}", pdf_styles["Normal"]))
            Story.append(PageBreak())
        
        # --- Insert Page Diagrams (for 'page gates') ---
        unique_page_nodes = {}
        for evt in self.top_events:
            for pg in self.get_page_nodes(evt):
                if pg.is_primary_instance:
                    unique_page_nodes[pg.unique_id] = pg

        if unique_page_nodes:
            Story.append(Paragraph("Page Diagrams:", pdf_styles["Heading2"]))
            Story.append(Spacer(1, 12))

        for page_node in unique_page_nodes.values():
            page_img = self.capture_page_diagram(page_node)
            if page_img is not None:
                buf = BytesIO()
                page_img.save(buf, format="PNG")
                buf.seek(0)
                desired_width, desired_height = scale_image(page_img)
                rl_page_img = RLImage(buf, width=desired_width, height=desired_height)
                Story.append(Paragraph(f"Page Diagram for: {page_node.name}", pdf_styles["Heading3"]))
                Story.append(Spacer(1, 12))
                Story.append(rl_page_img)
                Story.append(Spacer(1, 12))
            else:
                Story.append(Paragraph("A page diagram could not be captured.", pdf_styles["Normal"]))
                Story.append(Spacer(1, 12))

        # --- FMEA Tables ---
        if self.fmeas:
            Story.append(PageBreak())
            Story.append(Paragraph("FMEA Tables", pdf_styles["Heading2"]))
            Story.append(Spacer(1, 12))
            for fmea in self.fmeas:
                Story.append(Paragraph(fmea['name'], pdf_styles["Heading3"]))
                data = [["Component", "Parent", "Failure Mode", "Failure Effect", "Cause", "S", "O", "D", "RPN", "Requirements"]]
                for be in fmea['entries']:
                    parent = be.parents[0] if be.parents else None
                    if parent:
                        comp = parent.user_name if parent.user_name else f"Node {parent.unique_id}"
                        parent_name = comp
                    else:
                        comp = getattr(be, "fmea_component", "") or "N/A"
                        parent_name = ""
                    req_ids = "; ".join([r.get("id") for r in getattr(be, 'safety_requirements', [])])
                    rpn = be.fmea_severity * be.fmea_occurrence * be.fmea_detection
                    failure_mode = be.description or (be.user_name or f"BE {be.unique_id}")
                    row = [comp, parent_name, failure_mode, be.fmea_effect, getattr(be, 'fmea_cause', ''), be.fmea_severity, be.fmea_occurrence, be.fmea_detection, rpn, req_ids]
                    data.append(row)
                table = Table(data, repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('FONTSIZE', (0,0), (-1,-1), 8)
                ]))
                Story.append(table)
                Story.append(Spacer(1, 12))

        # --- FTA-FMEA Traceability Matrix ---
        basic_events = [n for n in self.get_all_nodes(self.root_node) if n.node_type.upper() == "BASIC EVENT"]
        if basic_events:
            Story.append(PageBreak())
            Story.append(Paragraph("FTA-FMEA Traceability", pdf_styles["Heading2"]))
            data = [["Basic Event", "Component"]]
            for be in basic_events:
                parent = be.parents[0] if be.parents else None
                comp = parent.user_name if parent and parent.user_name else (f"Node {parent.unique_id}" if parent else "N/A")
                data.append([be.user_name or f"BE {be.unique_id}", comp])
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 8)
            ]))
            Story.append(table)
            Story.append(Spacer(1, 12))

        # --- Final Build ---
        try:
            doc.build(Story)
        except Exception as e:
            messagebox.showerror("Report", f"Failed to generate PDF: {e}")
            return

        messagebox.showinfo(
            "Report",
            "PDF report generated!",
        )

    def generate_pdf_report(self):
        self._generate_pdf_report(include_assurance=True)

    def generate_pdf_without_assurance(self):
        """Generate a PDF report without the Prototype Assurance Level (PAL) pages."""
        self._generate_pdf_report(include_assurance=False)

    def capture_event_diagram(self, event_node):
        temp = tk.Toplevel(self.root)
        temp.withdraw()
        canvas = tk.Canvas(temp, bg="white", width=2000, height=2000)
        canvas.pack()
        self.draw_subtree_with_filter(canvas, event_node, self.get_all_nodes(event_node))
        canvas.delete("grid")
        canvas.update()
        bbox = canvas.bbox("all")
        if not bbox:
            temp.destroy()
            return None
        x, y, x2, y2 = bbox
        margin_left = 100
        margin_top  = 30
        new_x = x - margin_left
        new_y = y - margin_top
        new_width = (x2 - x) + 2 * margin_left
        new_height = (y2 - y) + 2 * margin_top
        ps = canvas.postscript(colormode="color", x=new_x, y=new_y, width=new_width, height=new_height)
        from io import BytesIO
        ps_bytes = BytesIO(ps.encode("utf-8"))
        try:
            img = Image.open(ps_bytes)
            img.load(scale=3)
        except Exception:
            img = None
        temp.destroy()
        return img.convert("RGB") if img else None

    def draw_subtree_with_filter(self, canvas, root_event, visible_nodes):
        self.draw_connections_subtree(canvas, root_event, set())
        for n in visible_nodes:
            self.draw_node_on_canvas_pdf(canvas, n)

    def draw_subtree(self, canvas, root_event):
        canvas.delete("all")
        self.draw_connections_subtree(canvas, root_event, set())
        for n in self.get_all_nodes(root_event):
            self.draw_node_on_canvas(canvas, n)
        canvas.config(scrollregion=canvas.bbox("all"))

    def draw_connections_subtree(self, canvas, node, drawn_ids):
        if id(node) in drawn_ids:
            return
        drawn_ids.add(id(node))
        if node.is_page and node.node_type.upper() != "TOP EVENT":
            return
        region_width = 100 * self.zoom
        parent_bottom = (node.x * self.zoom, node.y * self.zoom + 40 * self.zoom)
        N = len(node.children)
        for i, child in enumerate(node.children):
            parent_conn = (node.x * self.zoom - region_width/2 + (i+0.5)*(region_width/N), parent_bottom[1])
            child_top = (child.x * self.zoom, child.y * self.zoom - 45 * self.zoom)
            # Call the helper’s method instead of a global function.
            fta_drawing_helper.draw_90_connection(canvas, parent_conn, child_top,
                                                  outline_color="dimgray", line_width=1)
        for child in node.children:
            self.draw_connections_subtree(canvas, child, drawn_ids)
            
    def draw_node_on_canvas_pdf(self, canvas, node):
        # For cloned nodes, use the original's values.
        if not node.is_primary_instance and hasattr(node, "original") and node.original:
            base_label = node.original.display_label
            subtype = node.original.input_subtype or "N/A"
            equation_text = node.original.equation
            detailed_eq = node.original.detailed_equation
        else:
            base_label = node.display_label
            subtype = node.input_subtype or "N/A"
            equation_text = node.equation
            detailed_eq = node.detailed_equation

        # Extract the score type from the base label.
        # For example, if the base label is "Required Rigor [4]", score_type becomes "Required Rigor".
        score_type = base_label.split('[')[0].strip()

        fill_color = self.get_node_fill_color(node)
        eff_x = node.x * self.zoom
        eff_y = node.y * self.zoom

        # Decide what to show in the top text based on the configuration.
        if self.project_properties.get("pdf_detailed_formulas", True):
            # Detailed mode: show the score type and the node description.
            top_text = (f"Type: {node.node_type}\n"
                        f"Score: {score_type}\n"
                        f"Subtype: {subtype}\n"
                        f"Desc: {node.description}")
        else:
            # Score-only mode: show the discretized metric (as an integer, without decimals).
            if node.quant_value is not None:
                # Convert quant_value to float and discretize
                score_value = float(node.quant_value)
                discrete = AD_RiskAssessment_Helper.discretize_level(score_value)
            else:
                discrete = "N/A"
            top_text = (f"Type: {node.node_type}\n"
                        f"{score_type} = {discrete}\n"
                        f"Subtype: {subtype}")

        bottom_text = node.name
        node_type_upper = node.node_type.upper()

        if node.is_page:
            fta_drawing_helper.draw_triangle_shape(canvas, eff_x, eff_y, scale=40 * self.zoom,
                                                   top_text=top_text,
                                                   bottom_text=bottom_text,
                                                   fill=fill_color,
                                                   outline_color="dimgray",
                                                   line_width=1,
                                                   font_obj=self.diagram_font)
        elif node_type_upper in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
            fta_drawing_helper.draw_circle_event_shape(canvas, eff_x, eff_y, 45 * self.zoom,
                                                       top_text=top_text,
                                                       bottom_text=bottom_text,
                                                       fill=fill_color,
                                                       outline_color="dimgray",
                                                       line_width=1,
                                                       font_obj=self.diagram_font)
        elif node_type_upper in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
            if node.gate_type.upper() == "OR":
                fta_drawing_helper.draw_rotated_or_gate_clone_shape(canvas, eff_x, eff_y,
                                                                    scale=40 * self.zoom,
                                                                    top_text=top_text,
                                                                    bottom_text=bottom_text,
                                                                    fill=fill_color,
                                                                    outline_color="dimgray",
                                                                    line_width=1,
                                                                    font_obj=self.diagram_font)
            else:
                fta_drawing_helper.draw_rotated_and_gate_clone_shape(canvas, eff_x, eff_y,
                                                                     scale=40 * self.zoom,
                                                                     top_text=top_text,
                                                                     bottom_text=bottom_text,
                                                                     fill=fill_color,
                                                                     outline_color="dimgray",
                                                                     line_width=1,
                                                                     font_obj=self.diagram_font)
        else:
            fta_drawing_helper.draw_circle_event_shape(canvas, eff_x, eff_y, 45 * self.zoom,
                                                       top_text=top_text,
                                                       bottom_text=bottom_text,
                                                       fill=fill_color,
                                                       outline_color="dimgray",
                                                       line_width=1,
                                                       font_obj=self.diagram_font)

        # In detailed mode, also draw the equations.
        if self.project_properties.get("pdf_detailed_formulas", True):
            canvas.create_text(eff_x - 80 * self.zoom, eff_y - 15 * self.zoom,
                               text=equation_text, anchor="e", fill="gray",
                               font=self.diagram_font)
            canvas.create_text(eff_x - 80 * self.zoom, eff_y + 15 * self.zoom,
                               text=detailed_eq, anchor="e", fill="gray",
                               font=self.diagram_font)

    def save_diagram_png(self):
        margin = 50
        all_nodes = self.get_all_nodes(self.root_node)
        if not all_nodes:
            messagebox.showerror("Error", "No nodes to export.")
            return
        min_x = min(n.x for n in all_nodes) - margin
        min_y = min(n.y for n in all_nodes) - margin
        max_x = max(n.x for n in all_nodes) + margin
        max_y = max(n.y for n in all_nodes) + margin
        scale_factor = 4
        width = int((max_x - min_x) * scale_factor)
        height = int((max_y - min_y) * scale_factor)
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)
        grid_size = self.grid_size
        for x in range(0, int(max_x - min_x) + 1, grid_size):
            x_pos = int(x * scale_factor)
            draw.line([(x_pos, 0), (x_pos, height)], fill="#ddd")
        for y in range(0, int(max_y - min_y) + 1, grid_size):
            y_pos = int(y * scale_factor)
            draw.line([(0, y_pos), (width, y_pos)], fill="#ddd")
        try:
            font = ImageFont.truetype("arial.ttf", 10 * scale_factor)
        except IOError:
            font = ImageFont.load_default()
        for node in all_nodes:
            eff_x = int((node.x - min_x) * scale_factor)
            eff_y = int((node.y - min_y) * scale_factor)
            radius = int(45 * scale_factor)
            bbox = [eff_x - radius, eff_y - radius, eff_x + radius, eff_y + radius]
            node_color = self.get_node_fill_color(node)
            draw.ellipse(bbox, outline="dimgray", fill=node_color)
            text = node.name
            text_size = draw.textsize(text, font=font)
            text_x = eff_x - text_size[0] // 2
            text_y = eff_y - text_size[1] // 2
            draw.text((text_x, text_y), text, fill="black", font=font)
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png")])
        if file_path:
            try:
                img.save(file_path, "PNG")
                messagebox.showinfo("Saved", "High-resolution diagram exported as PNG.")
            except Exception as e:
                messagebox.showerror("Save Error", f"An error occurred: {e}")

    def on_treeview_click(self, event):
        sel = self.treeview.selection()
        if not sel:
            return
        try:
            node_id = int(self.treeview.item(sel[0], "tags")[0])
        except (IndexError, ValueError):
            return
        node = self.find_node_by_id_all(node_id)
        if node:
            self.open_page_diagram(node)

    def on_ctrl_mousewheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def new_model(self):
        if not messagebox.askyesno("New Model", "This will close the current project and start a new one. Continue?"):
            return

        AD_RiskAssessment_Helper.unique_node_id_counter = 1
        self.zoom = 1.0
        self.diagram_font.config(size=int(8 * self.zoom))

        # Close any open page diagrams.
        if hasattr(self, "page_diagram") and self.page_diagram is not None:
            self.close_page_diagram()

        # Clear the tree view.
        self.treeview.delete(*self.treeview.get_children())

        # Destroy the old canvas_frame and re-create it.
        if self.canvas_frame:
            self.canvas_frame.destroy()
        self.canvas_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(self.canvas_frame, stretch="always")

        # Use grid (instead of pack) to add the canvas and scrollbars.
        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.hbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.hbar.grid(row=1, column=0, sticky="ew")
        self.vbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set,
                           scrollregion=(0, 0, 2000, 2000))
        
        # Configure grid weights so that the canvas expands.
        self.canvas_frame.rowconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(0, weight=1)

        # Rebind canvas events.
        self.canvas.bind("<ButtonPress-3>", self.on_right_mouse_press)
        self.canvas.bind("<B3-Motion>", self.on_right_mouse_drag)
        self.canvas.bind("<ButtonRelease-3>", self.show_context_menu)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_mousewheel)

        global unique_node_id_counter
        unique_node_id_counter = 1
        self.top_events = []
        self.root_node = None
        self.selected_node = None

        new_root = FaultTreeNode("Vehicle Level Function", "TOP EVENT")
        new_root.x, new_root.y = 300, 200
        self.top_events.append(new_root)
        self.root_node = new_root
        self.fmea_entries = []
        self.fmeas = []
        self.update_views()
        self.set_last_saved_state()
        self.canvas.update()

    def compute_occurrence_counts(self):
        counts = {}
        visited = set()
        def rec(node):
            if node.unique_id in visited:
                counts[node.unique_id] += 1
            else:
                visited.add(node.unique_id)
                counts[node.unique_id] = 1
            for child in node.children:
                rec(child)
        rec(self.root_node)
        return counts

    def get_node_fill_color(self, node):
        # Use the original node's properties for clones.
        base_node = node if node.is_primary_instance else node.original
        label = base_node.display_label  # use original's display label
        if "Prototype Assurance Level (PAL)" in label:
            base_type = "Prototype Assurance Level (PAL)"
        elif "Maturity" in label:
            base_type = "Maturity"
        elif "Rigor" in label:
            base_type = "Rigor"
        elif "Confidence" in label:
            base_type = "Confidence"
        elif "Robustness" in label:
            base_type = "Robustness"
        else:
            base_type = "Other"
        subtype = base_node.input_subtype if base_node.input_subtype else "Default"
        color_mapping = {
            "Confidence": {"Function": "lightpink", "Human Task": "lightgreen", "Default": "lightpink"},
            "Robustness": {"Function": "orange", "Human Task": "pink", "Default": "orange"},
            "Maturity": {"Functionality": "lightyellow", "Default": "lightyellow"},
            "Rigor": {"Capability": "turquoise", "Safety Mechanism": "yellow", "Default": "turquoise"},
            "Prototype Assurance Level (PAL)": {"Vehicle Level Function": "pink", "Functionality": "lightyellow","Capability": "turquoise", "Safety Mechanism": "yellow"},
            "Other": {"Default": "lightblue"}
        }
        return color_mapping.get(base_type, {}).get(subtype, color_mapping.get(base_type, {}).get("Default", "lightblue"))

    def on_right_mouse_press(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def on_right_mouse_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def show_context_menu(self, event):
        x = self.canvas.canvasx(event.x) / self.zoom
        y = self.canvas.canvasy(event.y) / self.zoom
        clicked_node = None
        for n in self.get_all_nodes(self.root_node):
            radius = 60 if n.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"] else 45
            if (x - n.x)**2 + (y - n.y)**2 < radius**2:
                clicked_node = n
                break
        if not clicked_node:
            return
        self.selected_node = clicked_node
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Edit", command=lambda: self.edit_selected())
        menu.add_command(label="Remove Connection", command=lambda: self.remove_connection(clicked_node))
        menu.add_command(label="Delete Node", command=lambda: self.delete_node_and_subtree(clicked_node))
        menu.add_command(label="Remove Node", command=lambda: self.remove_node())
        menu.add_command(label="Copy", command=lambda: self.copy_node())
        menu.add_command(label="Cut", command=lambda: self.cut_node())
        menu.add_command(label="Paste", command=lambda: self.paste_node())
        menu.add_separator()
        menu.add_command(label="Edit User Name", command=lambda: self.edit_user_name())
        menu.add_command(label="Edit Description", command=lambda: self.edit_description())
        menu.add_command(label="Edit Rationale", command=lambda: self.edit_rationale())
        menu.add_command(label="Edit Value", command=lambda: self.edit_value())
        menu.add_command(label="Edit Gate Type", command=lambda: self.edit_gate_type())
        menu.add_command(label="Edit Severity", command=lambda: self.edit_severity())
        menu.add_command(label="Edit Controllability", command=lambda: self.edit_controllability())
        menu.add_command(label="Edit Page Flag", command=lambda: self.edit_page_flag())
        menu.add_separator()
        menu.add_command(label="Add Confidence", command=lambda: self.add_node_of_type("Confidence Level"))
        menu.add_command(label="Add Robustness", command=lambda: self.add_node_of_type("Robustness Score"))
        menu.add_command(label="Add Gate", command=lambda: self.add_node_of_type("GATE"))
        menu.tk_popup(event.x_root, event.y_root)

    def on_canvas_click(self, event):
        x = self.canvas.canvasx(event.x) / self.zoom
        y = self.canvas.canvasy(event.y) / self.zoom
        clicked_node = None
        for n in self.get_all_nodes(self.root_node):
            radius = 60 if n.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"] else 45
            if (x - n.x)**2 + (y - n.y)**2 < radius**2:
                clicked_node = n
                break
        self.selected_node = clicked_node
        if clicked_node:
            self.dragging_node = clicked_node
            self.drag_offset_x = x - clicked_node.x
            self.drag_offset_y = y - clicked_node.y
        else:
            self.dragging_node = None
        self.redraw_canvas()

    def on_canvas_double_click(self, event):
        x = self.canvas.canvasx(event.x) / self.zoom
        y = self.canvas.canvasy(event.y) / self.zoom
        clicked_node = None
        for n in self.get_all_nodes(self.root_node):
            radius = 60 if n.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"] else 45
            if (x - n.x)**2 + (y - n.y)**2 < radius**2:
                clicked_node = n
                break
        if clicked_node:
            if not clicked_node.is_primary_instance:
                self.open_page_diagram(getattr(clicked_node, "original", clicked_node))
            else:
                if clicked_node.is_page:
                    self.open_page_diagram(clicked_node)
                else:
                    EditNodeDialog(self.root, clicked_node, self)
            self.update_views()

    def on_canvas_drag(self, event):
        if self.dragging_node:
            x = self.canvas.canvasx(event.x) / self.zoom
            y = self.canvas.canvasy(event.y) / self.zoom
            new_x = x - self.drag_offset_x
            new_y = y - self.drag_offset_y
            dx = new_x - self.dragging_node.x
            dy = new_y - self.dragging_node.y
            self.dragging_node.x = new_x
            self.dragging_node.y = new_y
            if self.dragging_node.is_primary_instance:
                self.move_subtree(self.dragging_node, dx, dy)
            self.sync_nodes_by_id(self.dragging_node)
            self.redraw_canvas()

    def on_canvas_release(self, event):
        if self.dragging_node:
            self.dragging_node.x = round(self.dragging_node.x/self.grid_size)*self.grid_size
            self.dragging_node.y = round(self.dragging_node.y/self.grid_size)*self.grid_size
        self.dragging_node = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0

    def move_subtree(self, node, dx, dy):
        for child in node.children:
            child.x += dx
            child.y += dy
            self.move_subtree(child, dx, dy)

    def zoom_in(self):
        self.zoom *= 1.2
        self.diagram_font.config(size=int(8 * self.zoom))
        self.redraw_canvas()

    def zoom_out(self):
        self.zoom /= 1.2
        self.diagram_font.config(size=int(8 * self.zoom))
        self.redraw_canvas()

    def auto_arrange(self):
        horizontal_gap = 150
        vertical_gap = 100
        next_y = [100]
        def layout(node, depth):
            node.x = depth * horizontal_gap + 100
            if not node.children:
                node.y = next_y[0]
                next_y[0] += vertical_gap
            else:
                for child in node.children:
                    layout(child, depth+1)
                node.y = (node.children[0].y + node.children[-1].y) / 2
        layout(self.root_node, 0)
        self.update_views()

    def get_all_nodes_table(self,root_node):
        """
        Recursively traverse the entire fault tree starting from root_node without any filtering.
        Returns a list of all nodes.
        """
        collector = []
        def rec(n):
            collector.append(n)
            for child in n.children:
                rec(child)
        rec(root_node)
        return collector

    def get_all_nodes_in_model(self):
        """
        Return a list of *all* nodes across *all* top-level events in self.top_events.
        """
        all_nodes = []
        for te in self.top_events:
            nodes = self.get_all_nodes_table(te)  # your existing method for one root
            all_nodes.extend(nodes)
        return all_nodes

    def get_all_basic_events(self):
        """Return a list of all basic events across all top-level trees."""
        return [n for n in self.get_all_nodes_in_model() if n.node_type.upper() == "BASIC EVENT"]


    def get_all_nodes(self, node=None):
        if node is None:
            result = []
            for te in self.top_events:
                result.extend(self.get_all_nodes(te))
            return result

        visited = set()
        def rec(n):
            if n.unique_id in visited:
                return []
            visited.add(n.unique_id)
            # ---- Remove or comment out any code that returns [] if n is a page or if a parent is a page
            if n != self.root_node and any(parent.is_page for parent in n.parents):
                return []

            result = [n]
            for c in n.children:
                result.extend(rec(c))
            return result

        return rec(node)

    def update_views(self):
        self.treeview.delete(*self.treeview.get_children())
        for top_event in self.top_events:
            self.insert_node_in_tree("", top_event)
        # NEW: Compute the occurrence counts from the current tree:
        self.occurrence_counts = self.compute_occurrence_counts()

        if hasattr(self, "page_diagram") and self.page_diagram is not None:
            if self.page_diagram.canvas.winfo_exists():
                self.page_diagram.redraw_canvas()
            else:
                self.page_diagram = None
        elif hasattr(self, "canvas") and self.canvas.winfo_exists():
            if self.selected_node is not None:
                self.redraw_canvas()
            else:
                self.canvas.delete("all")

    def insert_node_in_tree(self, parent_item, node):
        # If the node has no parent (i.e. it's a top-level event), display it.
        if not node.parents or node.node_type.upper() == "TOP EVENT" or node.is_page:
            txt = node.name
            item_id = self.treeview.insert(parent_item, "end", text=txt, open=True, tags=(str(node.unique_id),))
            # Recursively insert all children regardless of their type.
            for child in node.children:
                self.insert_node_in_tree(item_id, child)
        else:
            # If the node is not top-level, still check its children.
            for child in node.children:
                self.insert_node_in_tree(parent_item, child)

    def redraw_canvas(self):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return
        self.canvas.delete("all")
        self.draw_grid()
        drawn_ids = set()
        for top_event in self.top_events:
            self.draw_connections(top_event, drawn_ids)
        all_nodes = []
        for top_event in self.top_events:
            all_nodes.extend(self.get_all_nodes(top_event))
        for node in all_nodes:
            self.draw_node(node)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def draw_grid(self):
        spacing = self.grid_size * self.zoom
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width < 10:
            width = 800
        if height < 10:
            height = 600
        for x in range(0, int(width), int(spacing)):
            self.canvas.create_line(x, 0, x, height, fill="#ddd", tags="grid")
        for y in range(0, int(height), int(spacing)):
            self.canvas.create_line(0, y, width, y, fill="#ddd", tags="grid")

    def create_diagram_image_without_grid(self):
        if hasattr(self, "canvas") and self.canvas.winfo_exists():
            target_canvas = self.canvas
        elif hasattr(self, "page_diagram") and self.page_diagram is not None:
            target_canvas = self.page_diagram.canvas
        else:
            return None
        grid_items = target_canvas.find_withtag("grid")
        target_canvas.delete("grid")
        target_canvas.update()
        bbox = target_canvas.bbox("all")
        if not bbox:
            return None
        x, y, w, h = bbox[0], bbox[1], bbox[2]-bbox[0], bbox[3]-bbox[1]
        ps = target_canvas.postscript(colormode="color", x=x, y=y, width=w, height=h)
        from io import BytesIO
        ps_bytes = BytesIO(ps.encode("utf-8"))
        img = Image.open(ps_bytes)
        img.load(scale=3)
        if target_canvas == self.canvas:
            self.redraw_canvas()
        else:
            self.page_diagram.redraw_canvas()
        return img.convert("RGB")

    def draw_connections(self, node, drawn_ids=set()):
        if id(node) in drawn_ids:
            return
        drawn_ids.add(id(node))
        if node.is_page and node.is_primary_instance:
            return
        if node.children:
            region_width = 100 * self.zoom
            parent_bottom = (node.x * self.zoom, node.y * self.zoom + 40 * self.zoom)
            N = len(node.children)
            for i, child in enumerate(node.children):
                parent_conn = (node.x * self.zoom - region_width/2 + (i+0.5)*(region_width/N), parent_bottom[1])
                child_top = (child.x * self.zoom, child.y * self.zoom - 45 * self.zoom)
                fta_drawing_helper.draw_90_connection(self.canvas, parent_conn, child_top, outline_color="dimgray", line_width=1)
            for child in node.children:
                self.draw_connections(child, drawn_ids)

    def draw_node(self, node):
        """
        Draws the given node on the main canvas.
        For clones, it always uses the original’s non-positional attributes (like display_label,
        description, etc.) so that any changes to the original are reflected on all clones.
        """
        # If the node is a clone, use its original for configuration (non-positional attributes)
        source = node if node.is_primary_instance else node.original

        # For display purposes, show the clone marker on the clone's display_label.
        if node.is_primary_instance:
            display_label = source.display_label
        else:
            display_label = source.display_label + " (clone)"

        # Build a short top_text string from the source's attributes.
        subtype_text = source.input_subtype if source.input_subtype else "N/A"
        top_text = (
            f"Type: {source.node_type}\n"
            f"Subtype: {subtype_text}\n"
            f"{display_label}\n"
            f"Desc: {source.description}\n\n"
            f"Rationale: {source.rationale}"
        )
        # For the bottom text, you may choose to display the node's name (which for a clone is
        # usually the same as the original’s name)
        bottom_text = source.name

        # Compute the effective position using the clone’s own (positional) values
        eff_x = node.x * self.zoom
        eff_y = node.y * self.zoom

        # Highlight if selected or in diff list
        if node == self.selected_node:
            outline_color = "red"
            line_width = 2
        elif node.unique_id in self.diff_nodes:
            outline_color = "blue"
            line_width = 2
        else:
            outline_color = "dimgray"
            line_width = 1

        # Determine the fill color (this function already uses the original's display_label)
        fill_color = self.get_node_fill_color(node)
        font_obj = self.diagram_font

        # For shape selection, use the source’s node type and gate type.
        node_type_upper = source.node_type.upper()

        if not node.is_primary_instance:
            # For clones, draw them in a “clone” style.
            if source.is_page:
                fta_drawing_helper.draw_triangle_shape(
                    self.canvas, eff_x, eff_y, scale=40 * self.zoom,
                    top_text=top_text, bottom_text=bottom_text,
                    fill=fill_color, outline_color=outline_color,
                    line_width=line_width, font_obj=font_obj
                )
            elif node_type_upper in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
                if source.gate_type.upper() == "OR":
                    fta_drawing_helper.draw_rotated_or_gate_clone_shape(
                        self.canvas, eff_x, eff_y, scale=40 * self.zoom,
                        top_text=top_text, bottom_text=bottom_text,
                        fill=fill_color, outline_color=outline_color,
                        line_width=line_width, font_obj=font_obj
                    )
                else:
                    fta_drawing_helper.draw_rotated_and_gate_clone_shape(
                        self.canvas, eff_x, eff_y, scale=40 * self.zoom,
                        top_text=top_text, bottom_text=bottom_text,
                        fill=fill_color, outline_color=outline_color,
                        line_width=line_width, font_obj=font_obj
                    )
            elif node_type_upper in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
                fta_drawing_helper.draw_circle_event_shape(
                    self.canvas, eff_x, eff_y, 45 * self.zoom,
                    top_text=top_text, bottom_text=bottom_text,
                    fill=fill_color, outline_color=outline_color,
                    line_width=line_width, font_obj=font_obj
                )
            else:
                fta_drawing_helper.draw_circle_event_shape(
                    self.canvas, eff_x, eff_y, 45 * self.zoom,
                    top_text=top_text, bottom_text=bottom_text,
                    fill=fill_color, outline_color=outline_color,
                    line_width=line_width, font_obj=font_obj
                )
        else:
            # Primary node: use normal drawing routines.
            if node_type_upper in ["TOP EVENT", "GATE", "RIGOR LEVEL"]:
                if source.is_page and source != self.root_node:
                    fta_drawing_helper.draw_triangle_shape(
                        self.canvas, eff_x, eff_y, scale=40 * self.zoom,
                        top_text=top_text, bottom_text=bottom_text,
                        fill=fill_color, outline_color=outline_color,
                        line_width=line_width, font_obj=font_obj
                    )
                else:
                    if source.gate_type.upper() == "OR":
                        fta_drawing_helper.draw_rotated_or_gate_shape(
                            self.canvas, eff_x, eff_y, scale=40 * self.zoom,
                            top_text=top_text, bottom_text=bottom_text,
                            fill=fill_color, outline_color=outline_color,
                            line_width=line_width, font_obj=font_obj
                        )
                    else:
                        fta_drawing_helper.draw_rotated_and_gate_shape(
                            self.canvas, eff_x, eff_y, scale=40 * self.zoom,
                            top_text=top_text, bottom_text=bottom_text,
                            fill=fill_color, outline_color=outline_color,
                            line_width=line_width, font_obj=font_obj
                        )
            elif node_type_upper in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
                fta_drawing_helper.draw_circle_event_shape(
                    self.canvas, eff_x, eff_y, 45 * self.zoom,
                    top_text=top_text, bottom_text=bottom_text,
                    fill=fill_color, outline_color=outline_color,
                    line_width=line_width, font_obj=font_obj
                )
            else:
                fta_drawing_helper.draw_circle_event_shape(
                    self.canvas, eff_x, eff_y, 45 * self.zoom,
                    top_text=top_text, bottom_text=bottom_text,
                    fill=fill_color, outline_color=outline_color,
                    line_width=line_width, font_obj=font_obj
                )

        # Draw any additional text (such as equations) from the source.
        if source.equation:
            self.canvas.create_text(
                eff_x - 80 * self.zoom, eff_y - 15 * self.zoom,
                text=source.equation, anchor="e", fill="gray",
                font=self.diagram_font
            )
        if source.detailed_equation:
            self.canvas.create_text(
                eff_x - 80 * self.zoom, eff_y + 15 * self.zoom,
                text=source.detailed_equation, anchor="e", fill="gray",
                font=self.diagram_font
            )

        # Finally, if the node appears multiple times, draw a shared marker.
        if self.occurrence_counts.get(node.unique_id, 0) > 1:
            marker_x = eff_x + 30 * self.zoom
            marker_y = eff_y - 30 * self.zoom
            fta_drawing_helper.draw_shared_marker(self.canvas, marker_x, marker_y, self.zoom)

        if self.review_data:
            unresolved = any(c.node_id == node.unique_id and not c.resolved for c in self.review_data.comments)
            if unresolved:
                self.canvas.create_oval(eff_x + 35 * self.zoom, eff_y + 35 * self.zoom,
                                        eff_x + 45 * self.zoom, eff_y + 45 * self.zoom,
                                        fill='yellow', outline='black')

        if self.review_data:
            unresolved = any(c.node_id == node.unique_id and not c.resolved for c in self.review_data.comments)
            if unresolved:
                self.canvas.create_oval(eff_x + 35 * self.zoom, eff_y + 35 * self.zoom,
                                        eff_x + 45 * self.zoom, eff_y + 45 * self.zoom,
                                        fill='yellow', outline='black')

        if self.review_data:
            unresolved = any(c.node_id == node.unique_id and not c.resolved for c in self.review_data.comments)
            if unresolved:
                self.canvas.create_oval(eff_x + 35 * self.zoom, eff_y + 35 * self.zoom,
                                        eff_x + 45 * self.zoom, eff_y + 45 * self.zoom,
                                        fill='yellow', outline='black')

        if self.review_data:
            unresolved = any(c.node_id == node.unique_id and not c.resolved for c in self.review_data.comments)
            if unresolved:
                self.canvas.create_oval(eff_x + 35 * self.zoom, eff_y + 35 * self.zoom,
                                        eff_x + 45 * self.zoom, eff_y + 45 * self.zoom,
                                        fill='yellow', outline='black')

    def find_node_by_id(self, node, unique_id, visited=None):
        if visited is None:
            visited = set()
        if node.unique_id in visited:
            return None
        visited.add(node.unique_id)
        if node.unique_id == unique_id:
            return node
        for c in node.children:
            res = self.find_node_by_id(c, unique_id, visited)
            if res:
                return res
        return None

    def is_descendant(self, node, possible_ancestor):
        if node == possible_ancestor:
            return True
        for p in node.parents:
            if self.is_descendant(p, possible_ancestor):
                return True
        return False

    def add_node_of_type(self, event_type):
        # If a node is selected, ensure it is a primary instance.
        if self.selected_node:
            if not self.selected_node.is_primary_instance:
                messagebox.showwarning("Invalid Operation", 
                    "Cannot add new elements to a clone node.\nPlease select the original node instead.")
                return
            parent_node = self.selected_node
        else:
            sel = self.treeview.selection()
            if sel:
                try:
                    node_id = int(self.treeview.item(sel[0], "tags")[0])
                except (IndexError, ValueError):
                    messagebox.showwarning("No selection", "Select a parent node from the tree.")
                    return
                parent_node = self.find_node_by_id_all(node_id)
            else:
                messagebox.showwarning("No selection", "Select a parent node to paste into.")
                return

        # Prevent adding to base events.
        if parent_node.node_type.upper() in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE", "BASIC EVENT"]:
            messagebox.showwarning("Invalid", "Base events cannot have children.")
            return

        # Now create the new node.
        if event_type.upper() == "CONFIDENCE LEVEL":
            new_node = FaultTreeNode("", "Confidence Level", parent=parent_node)
            new_node.quant_value = 1
        elif event_type.upper() == "ROBUSTNESS SCORE":
            new_node = FaultTreeNode("", "Robustness Score", parent=parent_node)
            new_node.quant_value = 1
        elif event_type.upper() == "GATE":
            new_node = FaultTreeNode("", "GATE", parent=parent_node)
            new_node.gate_type = "AND"
        elif event_type.upper() == "BASIC EVENT":
            new_node = FaultTreeNode("", "Basic Event", parent=parent_node)
            new_node.failure_prob = 0.0
        else:
            new_node = FaultTreeNode("", event_type, parent=parent_node)
        new_node.x = parent_node.x + 100
        new_node.y = parent_node.y + 100
        parent_node.children.append(new_node)
        new_node.parents.append(parent_node)
        self.update_views()


    def remove_node(self):
        sel = self.treeview.selection()
        target = None
        if sel:
            tags = self.treeview.item(sel[0], "tags")
            target = self.find_node_by_id(self.root_node, int(tags[0]))
        elif self.selected_node:
            target = self.selected_node
        if target and target != self.root_node:
            if target.parents:
                for p in target.parents:
                    if target in p.children:
                        p.children.remove(target)
                target.parents = []
            self.update_views()
        else:
            messagebox.showwarning("Invalid", "Cannot remove the root node.")

    def remove_connection(self, node):
        if node and node != self.root_node:
            if node.parents:
                for p in node.parents:
                    if node in p.children:
                        p.children.remove(node)
                node.parents = []
                if node not in self.top_events:
                    self.top_events.append(node)
                self.update_views()
                messagebox.showinfo("Remove Connection",
                                    f"Disconnected {node.name} from its parent(s) and made it a top-level event.")
            else:
                messagebox.showwarning("Remove Connection", "Node has no parent connection.")
        else:
            messagebox.showwarning("Remove Connection", "Cannot disconnect the root node.")

    def delete_node_and_subtree(self, node):
        if node:
            if node in self.top_events:
                self.top_events.remove(node)
            else:
                for p in node.parents:
                    if node in p.children:
                        p.children.remove(node)
                node.parents = []
            self.update_views()
            messagebox.showinfo("Delete Node", f"Deleted {node.name} and its subtree.")
        else:
            messagebox.showwarning("Delete Node", "Select a node to delete.")

    def calculate_overall(self):
        for top_event in self.top_events:
            AD_RiskAssessment_Helper.calculate_assurance_recursive(top_event, self.top_events)
        self.update_views()
        results = ""
        for top_event in self.top_events:
            if top_event.quant_value is not None:
                disc = AD_RiskAssessment_Helper.discretize_level(top_event.quant_value)
                results += (f"Top Event {top_event.display_label}\n"
                            f"(Continuous: {top_event.quant_value:.2f}, Discrete: {disc})\n\n")
        messagebox.showinfo("Calculation", results.strip())

    def calculate_pmfh(self):
        for te in self.top_events:
            AD_RiskAssessment_Helper.calculate_probability_recursive(te)
        self.update_views()
        results = ""
        for te in self.top_events:
            results += f"Top Event {te.name}: PMHF = {te.probability:.2e}\n"
        messagebox.showinfo("PMHF Calculation", results.strip())

    def show_requirements_matrix(self):
        """Display a matrix table of requirements vs. basic events."""
        basic_events = [n for n in self.get_all_nodes(self.root_node)
                        if n.node_type.upper() == "BASIC EVENT"]
        reqs = list(global_requirements.values())
        reqs.sort(key=lambda r: r.get("req_type", ""))

        win = tk.Toplevel(self.root)
        win.title("Requirements Matrix")

        columns = ["Req ID", "ASIL", "Type", "Text"] + [be.user_name or f"BE {be.unique_id}" for be in basic_events]
        tree = ttk.Treeview(win, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120 if col not in ["Text"] else 300, anchor="center")
        tree.pack(fill=tk.BOTH, expand=True)

        for req in reqs:
            row = [req.get("id", ""), req.get("asil", ""), req.get("req_type", ""), req.get("text", "")]
            for be in basic_events:
                linked = any(r.get("id") == req.get("id") for r in getattr(be, "safety_requirements", []))
                row.append("X" if linked else "")
            tree.insert("", "end", values=row)

    def show_fmea_list(self):
        win = tk.Toplevel(self.root)
        win.title("FMEA List")
        listbox = tk.Listbox(win, height=10, width=40)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for fmea in self.fmeas:
            listbox.insert(tk.END, fmea['name'])

        def open_selected(event=None):
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            win.destroy()
            self.show_fmea_table(self.fmeas[idx])

        def add_fmea():
            name = simpledialog.askstring("New FMEA", "Enter FMEA name:")
            if name:
                file_name = f"fmea_{name}.csv"
                self.fmeas.append({'name': name, 'entries': [], 'file': file_name})
                listbox.insert(tk.END, name)

        def delete_fmea():
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            del self.fmeas[idx]
            listbox.delete(idx)

        listbox.bind("<Double-1>", open_selected)
        btn_frame = ttk.Frame(win)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(btn_frame, text="Open", command=open_selected).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Add", command=add_fmea).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Delete", command=delete_fmea).pack(fill=tk.X)

    class FMEARowDialog(simpledialog.Dialog):
        def __init__(self, parent, node, app, fmea_entries):
            self.node = node
            self.app = app
            self.fmea_entries = fmea_entries
            super().__init__(parent, title="Edit FMEA Entry")
            self.app.selected_node = node

        def body(self, master):
            self.resizable(False, False)

            ttk.Label(master, text="Component:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
            if self.node.parents:
                comp = self.node.parents[0].user_name or f"Node {self.node.parents[0].unique_id}"
            else:
                comp = getattr(self.node, "fmea_component", "")
            comp_names = set()
            basic_events = self.app.get_all_basic_events()
            for be in basic_events + self.fmea_entries:
                parent = be.parents[0] if be.parents else None
                if parent and parent.user_name:
                    comp_names.add(parent.user_name)
                else:
                    name = getattr(be, "fmea_component", "")
                    if name:
                        comp_names.add(name)
            self.comp_var = tk.StringVar(value=comp)
            self.comp_combo = ttk.Combobox(master, textvariable=self.comp_var,
                                           values=sorted(comp_names), width=30)
            self.comp_combo.grid(row=0, column=1, padx=5, pady=5)

            ttk.Label(master, text="Failure Mode:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
            # Include failure modes from both the FTA and any FMEA specific
            # entries so the combo box always lists all available modes.
            mode_names = [
                be.description or (be.user_name or f"BE {be.unique_id}")
                for be in basic_events + self.fmea_entries
            ]
            self.mode_var = tk.StringVar(value=self.node.description or self.node.user_name)
            self.mode_combo = ttk.Combobox(master, textvariable=self.mode_var,
                                          values=mode_names, width=30)
            self.mode_combo.grid(row=1, column=1, padx=5, pady=5)

            ttk.Label(master, text="Failure Effect:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
            self.effect_text = tk.Text(master, width=30, height=3)
            self.effect_text.insert("1.0", self.node.fmea_effect)
            self.effect_text.grid(row=2, column=1, padx=5, pady=5)

            ttk.Label(master, text="Potential Cause:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
            self.cause_text = tk.Text(master, width=30, height=3)
            self.cause_text.insert("1.0", getattr(self.node, 'fmea_cause', ''))
            self.cause_text.grid(row=3, column=1, padx=5, pady=5)

            ttk.Label(master, text="Severity (1-10):").grid(row=4, column=0, sticky="e", padx=5, pady=5)
            self.sev_spin = tk.Spinbox(master, from_=1, to=10, width=5)
            self.sev_spin.delete(0, tk.END)
            self.sev_spin.insert(0, str(self.node.fmea_severity))
            self.sev_spin.grid(row=4, column=1, sticky="w", padx=5, pady=5)

            ttk.Label(master, text="Occurrence (1-10):").grid(row=5, column=0, sticky="e", padx=5, pady=5)
            self.occ_spin = tk.Spinbox(master, from_=1, to=10, width=5)
            self.occ_spin.delete(0, tk.END)
            self.occ_spin.insert(0, str(self.node.fmea_occurrence))
            self.occ_spin.grid(row=5, column=1, sticky="w", padx=5, pady=5)

            ttk.Label(master, text="Detection (1-10):").grid(row=6, column=0, sticky="e", padx=5, pady=5)
            self.det_spin = tk.Spinbox(master, from_=1, to=10, width=5)
            self.det_spin.delete(0, tk.END)
            self.det_spin.insert(0, str(self.node.fmea_detection))
            self.det_spin.grid(row=6, column=1, sticky="w", padx=5, pady=5)

            ttk.Label(master, text="Requirements:").grid(row=7, column=0, sticky="ne", padx=5, pady=5)
            self.req_frame = ttk.Frame(master)
            self.req_frame.grid(row=7, column=1, padx=5, pady=5, sticky="w")
            self.req_listbox = tk.Listbox(self.req_frame, height=4, width=40)
            self.req_listbox.grid(row=0, column=0, columnspan=3, sticky="w")
            if not hasattr(self.node, "safety_requirements"):
                self.node.safety_requirements = []
            for req in self.node.safety_requirements:
                desc = f"[{req['req_type']}] [{req.get('asil','')}] {req['text']}"
                self.req_listbox.insert(tk.END, desc)
            ttk.Button(self.req_frame, text="Add New", command=self.add_safety_requirement).grid(row=1, column=0, padx=2, pady=2)
            ttk.Button(self.req_frame, text="Edit", command=self.edit_safety_requirement).grid(row=1, column=1, padx=2, pady=2)
            ttk.Button(self.req_frame, text="Delete", command=self.delete_safety_requirement).grid(row=1, column=2, padx=2, pady=2)
            ttk.Button(self.req_frame, text="Add Existing", command=self.add_existing_requirement).grid(row=1, column=3, padx=2, pady=2)
            ttk.Button(self.req_frame, text="Comment", command=self.comment_requirement).grid(row=1, column=4, padx=2, pady=2)
            ttk.Button(self.req_frame, text="Comment FMEA", command=self.comment_fmea).grid(row=1, column=5, padx=2, pady=2)
            return self.effect_text

        def apply(self):
            comp = self.comp_var.get()
            if self.node.parents:
                self.node.parents[0].user_name = comp
            # Always store the component name so it can be restored on load
            self.node.fmea_component = comp
            self.node.description = self.mode_var.get()
            self.node.fmea_effect = self.effect_text.get("1.0", "end-1c")
            self.node.fmea_cause = self.cause_text.get("1.0", "end-1c")
            try:
                self.node.fmea_severity = int(self.sev_spin.get())
            except ValueError:
                self.node.fmea_severity = 1
            try:
                self.node.fmea_occurrence = int(self.occ_spin.get())
            except ValueError:
                self.node.fmea_occurrence = 1
            try:
                self.node.fmea_detection = int(self.det_spin.get())
            except ValueError:
                self.node.fmea_detection = 1

        def add_existing_requirement(self):
            global global_requirements
            if not global_requirements:
                messagebox.showinfo("No Existing Requirements", "There are no existing requirements to add.")
                return
            dialog = EditNodeDialog.SelectExistingRequirementsDialog(self, title="Select Existing Requirements")
            if dialog.result:
                if not hasattr(self.node, "safety_requirements"):
                    self.node.safety_requirements = []
                for req_id in dialog.result:
                    req = global_requirements.get(req_id)
                    if req and not any(r["id"] == req_id for r in self.node.safety_requirements):
                        self.node.safety_requirements.append(req)
                        desc = f"[{req['req_type']}] [{req.get('asil','')}] {req['text']}"
                self.req_listbox.insert(tk.END, desc)
            else:
                messagebox.showinfo("No Selection", "No existing requirements were selected.")

        def comment_requirement(self):
            sel = self.req_listbox.curselection()
            if not sel:
                messagebox.showwarning("Comment", "Select a requirement")
                return
            req = self.node.safety_requirements[sel[0]]
            self.app.selected_node = self.node
            # include the node id as well so the toolbox has full context
            self.app.comment_target = ("requirement", self.node.unique_id, req.get("id"))
            self.app.open_review_toolbox()

        def comment_fmea(self):
            self.app.selected_node = self.node
            self.app.comment_target = ("fmea", self.node.unique_id)
            self.app.open_review_toolbox()


        def add_safety_requirement(self):
            global global_requirements
            dialog = EditNodeDialog.RequirementDialog(self, title="Add Safety Requirement")
            if dialog.result is None or dialog.result["text"] == "":
                return
            custom_id = dialog.result.get("custom_id", "").strip()
            if not custom_id:
                custom_id = str(uuid.uuid4())
            if custom_id in global_requirements:
                req = global_requirements[custom_id]
                req["req_type"] = dialog.result["req_type"]
                req["text"] = dialog.result["text"]
                req["asil"] = dialog.result.get("asil", "QM")
            else:
                req = {
                    "id": custom_id,
                    "req_type": dialog.result["req_type"],
                    "text": dialog.result["text"],
                    "custom_id": custom_id,
                    "asil": dialog.result.get("asil", "QM")
                }
                global_requirements[custom_id] = req
            if not hasattr(self.node, "safety_requirements"):
                self.node.safety_requirements = []
            if not any(r["id"] == custom_id for r in self.node.safety_requirements):
                self.node.safety_requirements.append(req)
                desc = f"[{req['req_type']}] [{req.get('asil','')}] {req['text']}"
                self.req_listbox.insert(tk.END, desc)

        def edit_safety_requirement(self):
            selected = self.req_listbox.curselection()
            if not selected:
                messagebox.showwarning("Edit Requirement", "Select a requirement to edit.")
                return
            index = selected[0]
            current_req = self.node.safety_requirements[index]
            initial_req = current_req.copy()
            dialog = EditNodeDialog.RequirementDialog(self, title="Edit Safety Requirement", initial_req=initial_req)
            if dialog.result is None or dialog.result["text"] == "":
                return
            new_custom_id = dialog.result["custom_id"].strip() or current_req.get("custom_id") or current_req.get("id") or str(uuid.uuid4())
            current_req["req_type"] = dialog.result["req_type"]
            current_req["text"] = dialog.result["text"]
            current_req["asil"] = dialog.result.get("asil", "QM")
            current_req["custom_id"] = new_custom_id
            current_req["id"] = new_custom_id
            global_requirements[new_custom_id] = current_req
            self.node.safety_requirements[index] = current_req
            self.req_listbox.delete(index)
            desc = f"[{current_req['req_type']}] [{current_req.get('asil','')}] {current_req['text']}"
            self.req_listbox.insert(index, desc)

        def delete_safety_requirement(self):
            selected = self.req_listbox.curselection()
            if not selected:
                messagebox.showwarning("Delete Requirement", "Select a requirement to delete.")
                return
            index = selected[0]
            del self.node.safety_requirements[index]
            self.req_listbox.delete(index)

    class SelectBaseEventDialog(simpledialog.Dialog):
        def __init__(self, parent, events, allow_new=False):
            self.events = events
            self.allow_new = allow_new
            self.selected = None
            super().__init__(parent, title="Select Base Event")

        def body(self, master):
            self.listbox = tk.Listbox(master, height=10, width=40)
            for be in self.events:
                label = be.description or (be.user_name or f"BE {be.unique_id}")
                self.listbox.insert(tk.END, label)
            if self.allow_new:
                self.listbox.insert(tk.END, "<Create New Failure Mode>")
            self.listbox.grid(row=0, column=0, padx=5, pady=5)
            return self.listbox

        def apply(self):
            sel = self.listbox.curselection()
            if sel:
                idx = sel[0]
                if self.allow_new and idx == len(self.events):
                    self.selected = "NEW"
                else:
                    self.selected = self.events[idx]

    def show_fmea_table(self, fmea=None):
        """Display an editable AIAG-compliant FMEA table."""
        basic_events = self.get_all_basic_events()
        entries = self.fmea_entries if fmea is None else fmea['entries']
        win = tk.Toplevel(self.root)
        title = f"FMEA Table - {fmea['name']}" if fmea else "FMEA Table"
        win.title(title)

        # give the table a nicer look similar to professional FMEA tools
        style = ttk.Style(win)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "FMEA.Treeview",
            font=("Segoe UI", 10),
            rowheight=22,
        )
        style.configure(
            "FMEA.Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#d0d0d0",
        )

        columns = [
            "Component",
            "Parent",
            "Failure Mode",
            "Failure Effect",
            "Cause",
            "S",
            "O",
            "D",
            "RPN",
            "Requirements",
        ]
        btn_frame = ttk.Frame(win)
        btn_frame.pack(side=tk.TOP, pady=2)
        add_btn = ttk.Button(btn_frame, text="Add Failure Mode")
        add_btn.pack(side=tk.LEFT, padx=2)
        remove_btn = ttk.Button(btn_frame, text="Remove from FMEA")
        remove_btn.pack(side=tk.LEFT, padx=2)
        del_btn = ttk.Button(btn_frame, text="Delete Selected")
        del_btn.pack(side=tk.LEFT, padx=2)
        comment_btn = ttk.Button(btn_frame, text="Comment")
        comment_btn.pack(side=tk.LEFT, padx=2)

        tree_frame = ttk.Frame(win)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            style="FMEA.Treeview",
        )
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        for col in columns:
            tree.heading(col, text=col)
            width = 120
            if col in ["Requirements", "Failure Effect", "Cause"]:
                width = 200
            elif col == "Parent":
                width = 150
            tree.column(col, width=width, anchor="center")
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # alternating row colours and high RPN highlight
        tree.tag_configure("component", background="#e2e2e2", font=("Segoe UI", 10, "bold"))
        tree.tag_configure("evenrow", background="#ffffff")
        tree.tag_configure("oddrow", background="#f5f5f5")
        tree.tag_configure("highrpn", background="#ffe6e6")

        node_map = {}
        comp_items = {}

        def refresh_tree():
            tree.delete(*tree.get_children())
            node_map.clear()
            comp_items.clear()
            # remove any duplicate nodes based on unique_id
            unique = {}
            for be in entries:
                unique[be.unique_id] = be
            entries[:] = list(unique.values())
            events = entries

            for idx, be in enumerate(events):
                parent = be.parents[0] if be.parents else None
                if parent:
                    comp = parent.user_name if parent.user_name else f"Node {parent.unique_id}"
                    parent_name = comp
                else:
                    comp = getattr(be, "fmea_component", "") or "N/A"
                    parent_name = ""
                if comp not in comp_items:
                    comp_items[comp] = tree.insert(
                        "",
                        "end",
                        text=comp,
                        values=[comp, "", "", "", "", "", "", "", "", ""],
                        tags=("component",),
                    )
                comp_iid = comp_items[comp]
                req_ids = "; ".join(
                    [f"{req['req_type']}:{req['text']}" for req in getattr(be, "safety_requirements", [])]
                )
                rpn = be.fmea_severity * be.fmea_occurrence * be.fmea_detection
                failure_mode = be.description or (be.user_name or f"BE {be.unique_id}")
                vals = [
                    "",
                    parent_name,
                    failure_mode,
                    be.fmea_effect,
                    be.fmea_cause,
                    be.fmea_severity,
                    be.fmea_occurrence,
                    be.fmea_detection,
                    rpn,
                    req_ids,
                ]
                tags = ["evenrow" if idx % 2 == 0 else "oddrow"]
                if rpn >= 100:
                    tags.append("highrpn")
                iid = tree.insert(comp_iid, "end", text="", values=vals, tags=tags)
                node_map[iid] = be
            for iid in comp_items.values():
                tree.item(iid, open=True)

        refresh_tree()

        def on_double(event):
            sel = tree.focus()
            node = node_map.get(sel)
            if node:
                self.FMEARowDialog(win, node, self, entries)
                refresh_tree()

        tree.bind("<Double-1>", on_double)

        def add_failure_mode():
            dialog = self.SelectBaseEventDialog(win, basic_events, allow_new=True)
            node = dialog.selected
            if node == "NEW":
                node = FaultTreeNode("", "Basic Event")
                entries.append(node)
                self.FMEARowDialog(win, node, self, entries)
            elif node:
                # gather all failure modes under the same component/parent
                if node.parents:
                    parent_id = node.parents[0].unique_id
                    related = [
                        be
                        for be in basic_events
                        if be.parents and be.parents[0].unique_id == parent_id
                    ]
                else:
                    comp = getattr(node, "fmea_component", "")
                    related = [
                        be
                        for be in basic_events
                        if not be.parents and getattr(be, "fmea_component", "") == comp
                    ]
                if node not in related:
                    related.append(node)
                existing_ids = {be.unique_id for be in entries}
                for be in related:
                    if be.unique_id not in existing_ids:
                        entries.append(be)
                        existing_ids.add(be.unique_id)
                    self.FMEARowDialog(win, be, self, entries)
            refresh_tree()

        add_btn.config(command=add_failure_mode)

        def remove_from_fmea():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Remove Entry", "Select a row to remove.")
                return
            for iid in sel:
                node = node_map.get(iid)
                if node in entries:
                    entries.remove(node)
            refresh_tree()

        remove_btn.config(command=remove_from_fmea)

        def delete_failure_mode():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Delete Failure Mode", "Select a row to delete.")
                return
            if not messagebox.askyesno("Delete Failure Mode", "Remove selected failure modes from the FMEA?"):
                return
            for iid in sel:
                node = node_map.get(iid)
                if node in entries:
                    entries.remove(node)
            refresh_tree()

        del_btn.config(command=delete_failure_mode)

        def comment_fmea_entry():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Comment", "Select a row to comment.")
                return
            node = node_map.get(sel[0])
            if not node:
                return
            self.selected_node = node
            self.comment_target = ("fmea", node.unique_id)
            self.open_review_toolbox()

        comment_btn.config(command=comment_fmea_entry)

        def on_close():
            if fmea is not None:
                self.export_fmea_to_csv(fmea, fmea['file'])
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)

    def export_fmea_to_csv(self, fmea, path):
        columns = ["Component", "Parent", "Failure Mode", "Failure Effect", "Cause", "S", "O", "D", "RPN", "Requirements"]
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for be in fmea['entries']:
                parent = be.parents[0] if be.parents else None
                if parent:
                    comp = parent.user_name if parent.user_name else f"Node {parent.unique_id}"
                    if parent.description:
                        comp = f"{comp} - {parent.description}"
                    parent_name = parent.user_name if parent.user_name else f"Node {parent.unique_id}"
                else:
                    comp = getattr(be, "fmea_component", "") or "N/A"
                    parent_name = ""
                req_ids = "; ".join([f"{req['req_type']}:{req['text']}" for req in getattr(be, 'safety_requirements', [])])
                rpn = be.fmea_severity * be.fmea_occurrence * be.fmea_detection
                failure_mode = be.description or (be.user_name or f"BE {be.unique_id}")
                row = [comp, parent_name, failure_mode, be.fmea_effect, be.fmea_cause, be.fmea_severity, be.fmea_occurrence, be.fmea_detection, rpn, req_ids]
                writer.writerow(row)


    def show_traceability_matrix(self):
        """Display a traceability matrix linking FTA basic events to FMEA components."""
        basic_events = [n for n in self.get_all_nodes(self.root_node)
                        if n.node_type.upper() == "BASIC EVENT"]
        win = tk.Toplevel(self.root)
        win.title("FTA-FMEA Traceability")
        columns = ["Basic Event", "Component"]
        tree = ttk.Treeview(win, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200, anchor="center")
        tree.pack(fill=tk.BOTH, expand=True)

        for be in basic_events:
            parent = be.parents[0] if be.parents else None
            comp = parent.user_name if parent and parent.user_name else (f"Node {parent.unique_id}" if parent else "N/A")
            tree.insert("", "end", values=[be.user_name or f"BE {be.unique_id}", comp])

    def collect_requirements_recursive(self, node):
        reqs = list(getattr(node, "safety_requirements", []))
        for child in node.children:
            reqs.extend(self.collect_requirements_recursive(child))
        return reqs

    def show_safety_goals_matrix(self):
        """Display safety goals and derived requirements in a tree view."""
        win = tk.Toplevel(self.root)
        win.title("Safety Goals Matrix")
        tree = ttk.Treeview(win, columns=["ID", "ASIL", "Text"], show="tree headings")
        tree.heading("ID", text="Requirement ID")
        tree.heading("ASIL", text="ASIL")
        tree.heading("Text", text="Text")
        tree.column("ID", width=120)
        tree.column("ASIL", width=60)
        tree.column("Text", width=300)
        tree.pack(fill=tk.BOTH, expand=True)

        for te in self.top_events:
            sg_text = te.safety_goal_description or (te.user_name or f"SG {te.unique_id}")
            sg_id = te.user_name or f"SG {te.unique_id}"
            parent_iid = tree.insert("", "end", text=sg_text,
                                    values=[sg_id, te.safety_goal_asil, sg_text])
            reqs = self.collect_requirements_recursive(te)
            seen_ids = set()
            for req in reqs:
                req_id = req.get("id")
                if req_id in seen_ids:
                    continue
                seen_ids.add(req_id)
                tree.insert(
                    parent_iid,
                    "end",
                    text="",
                    values=[req_id, req.get("asil", ""), req.get("text", "")],
                )

    def export_safety_goal_requirements(self):
        """Export requirements traced to safety goals including their ASIL."""
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return

        columns = ["Safety Goal", "SG ASIL", "Requirement ID", "Req ASIL", "Text"]
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for te in self.top_events:
                sg_text = te.safety_goal_description or (te.user_name or f"SG {te.unique_id}")
                sg_asil = te.safety_goal_asil
                reqs = self.collect_requirements_recursive(te)
                seen = set()
                for req in reqs:
                    rid = req.get("id")
                    if rid in seen:
                        continue
                    seen.add(rid)
                    writer.writerow([sg_text, sg_asil, rid, req.get("asil", ""), req.get("text", "")])
        messagebox.showinfo("Export", "Safety goal requirements exported.")


    def copy_node(self):
        if self.selected_node and self.selected_node != self.root_node:
            self.clipboard_node = self.selected_node
            self.cut_mode = False
        else:
            messagebox.showwarning("Copy", "Select a non-root node to copy.")

    def cut_node(self):
        if self.selected_node:
            self.clipboard_node = self.selected_node
            self.cut_mode = True
            self.clipboard_node.is_cut = True
        else:
            messagebox.showwarning("Cut", "Select a node to cut.")

    def paste_node(self):
        # 1) Determine target from selection or current selected node.
        target = None
        sel = self.treeview.selection()
        if sel:
            tags = self.treeview.item(sel[0], "tags")
            if tags:
                target = self.find_node_by_id(self.root_node, int(tags[0]))
        if not target:
            target = self.selected_node
        if not target:
            messagebox.showwarning("Paste", "Select a target node to paste into.")
            return

        # 2) Do not allow pasting into base events.
        if target.node_type.upper() in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
            messagebox.showwarning("Paste", "Cannot paste into a base event.")
            return

        # 3) Always use the primary instance of target.
        if not target.is_primary_instance:
            target = target.original

        # 4) Ensure clipboard is not empty.
        if not self.clipboard_node:
            messagebox.showwarning("Paste", "Clipboard is empty.")
            return

        # 5) Prevent self-pasting.
        if target.unique_id == self.clipboard_node.unique_id:
            messagebox.showwarning("Paste", "Cannot paste a node onto itself.")
            return
        for child in target.children:
            if child.unique_id == self.clipboard_node.unique_id:
                messagebox.showwarning("Paste", "This node is already a child of the target.")
                return

        # 6) If in cut mode, update parent's pointer, remove from top_events, and update coordinates.
        if self.cut_mode:
            if self.clipboard_node in self.top_events:
                self.top_events.remove(self.clipboard_node)
            for p in list(self.clipboard_node.parents):
                if self.clipboard_node in p.children:
                    p.children.remove(self.clipboard_node)
            self.clipboard_node.parents = []
            if self.clipboard_node.node_type.upper() == "TOP EVENT":
                # Demote top events so they no longer show in the tree.
                self.clipboard_node.node_type = "RIGOR LEVEL"
                self.clipboard_node.severity = None
                self.clipboard_node.is_page = False
                self.clipboard_node.input_subtype = "Capability"
            self.clipboard_node.is_primary_instance = True
            target.children.append(self.clipboard_node)
            self.clipboard_node.parents.append(target)
            # NEW: Update its position so it is offset relative to the new parent.
            self.clipboard_node.x = target.x + 100
            self.clipboard_node.y = target.y + 100
            # (Optional: remove any clone marker from its label.)
            self.clipboard_node.display_label = self.clipboard_node.display_label.replace(" (clone)", "")
            self.clipboard_node = None
            self.cut_mode = False
            messagebox.showinfo("Paste", "Node moved successfully (cut & pasted).")
        else:
            # 7) Copy branch: create a clone and attach it.
            cloned_node = self.clone_node_preserving_id(self.clipboard_node)
            target.children.append(cloned_node)
            cloned_node.parents.append(target)
            # NEW: Also update the cloned node’s position relative to the target.
            cloned_node.x = target.x + 100
            cloned_node.y = target.y + 100
            messagebox.showinfo("Paste", "Node pasted successfully (copied).")

        # 8) Recalculate and update views.
        AD_RiskAssessment_Helper.calculate_assurance_recursive(
            self.root_node,
            self.top_events,
        )
        self.update_views()
 
    def clone_node_preserving_id(self, node):
        # Create a new node with the same properties, but assign a new unique ID.
        new_node = FaultTreeNode(node.user_name, node.node_type)
        new_node.unique_id = AD_RiskAssessment_Helper.get_next_unique_id()
        new_node.quant_value = node.quant_value
        new_node.gate_type = node.gate_type
        new_node.description = node.description
        new_node.rationale = node.rationale
        # NEW: Offset the new node relative to the original.
        new_node.x = node.x + 100  
        new_node.y = node.y + 100
        new_node.severity = node.severity
        new_node.input_subtype = node.input_subtype
        new_node.display_label = node.display_label  # (do not append " (clone)" in the copy branch if you prefer)
        new_node.equation = node.equation
        new_node.detailed_equation = node.detailed_equation
        new_node.is_page = node.is_page
        new_node.is_primary_instance = False
        # Set the clone’s "original" pointer: if the original was primary, use it; otherwise, use its original.
        new_node.original = node if node.is_primary_instance else node.original
        new_node.children = []
        return new_node

    def sync_nodes_by_id(self, updated_node):
        # Always work with the primary instance.
        if not updated_node.is_primary_instance and updated_node.original:
            updated_node = updated_node.original
        updated_primary_id = updated_node.unique_id

        for node in self.get_all_nodes(self.root_node):
            # Skip the updated node itself.
            if node is updated_node:
                continue

            if node.is_primary_instance:
                if node.unique_id == updated_primary_id:
                    node.node_type = updated_node.node_type
                    node.user_name = updated_node.user_name
                    node.description = updated_node.description
                    node.rationale = updated_node.rationale
                    node.quant_value = updated_node.quant_value
                    node.gate_type = updated_node.gate_type
                    node.severity = updated_node.severity
                    node.input_subtype = updated_node.input_subtype
                    node.display_label = updated_node.display_label
                    node.equation = updated_node.equation
                    node.detailed_equation = updated_node.detailed_equation
                    node.is_page = updated_node.is_page
            else:
                # Use the original pointer to compare.
                if node.original and node.original.unique_id == updated_primary_id:
                    node.user_name = updated_node.user_name
                    node.description = updated_node.description
                    node.rationale = updated_node.rationale
                    node.quant_value = updated_node.quant_value
                    node.gate_type = updated_node.gate_type
                    node.severity = updated_node.severity
                    node.input_subtype = updated_node.input_subtype
                    # Append a marker to the display label to indicate this is a clone.
                    node.display_label = updated_node.display_label + " (clone)"
                    node.equation = updated_node.equation
                    node.detailed_equation = updated_node.detailed_equation
                    # **The key change: update the page flag on clones as well.**
                    node.is_page = updated_node.is_page

    def edit_user_name(self):
        if self.selected_node:
            new_name = simpledialog.askstring("Edit User Name", "Enter new user name:", initialvalue=self.selected_node.user_name)
            if new_name is not None:
                self.selected_node.user_name = new_name.strip()
                self.update_views()
        else:
            messagebox.showwarning("Edit User Name", "Select a node first.")

    def edit_description(self):
        if self.selected_node:
            new_desc = simpledialog.askstring("Edit Description", "Enter new description:", initialvalue=self.selected_node.description)
            if new_desc is not None:
                self.selected_node.description = new_desc
                self.update_views()
        else:
            messagebox.showwarning("Edit Description", "Select a node first.")

    def edit_rationale(self):
        if self.selected_node:
            new_rat = simpledialog.askstring("Edit Rationale", "Enter new rationale:", initialvalue=self.selected_node.rationale)
            if new_rat is not None:
                self.selected_node.rationale = new_rat
                self.update_views()
        else:
            messagebox.showwarning("Edit Rationale", "Select a node first.")

    def edit_value(self):
        if self.selected_node and self.selected_node.node_type.upper() in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
            try:
                new_val = simpledialog.askfloat("Edit Value", "Enter new value (1-5):", initialvalue=self.selected_node.quant_value)
                if new_val is not None and 1 <= new_val <= 5:
                    self.selected_node.quant_value = new_val
                    self.update_views()
                else:
                    messagebox.showerror("Error", "Value must be between 1 and 5.")
            except Exception:
                messagebox.showerror("Error", "Invalid input.")
        else:
            messagebox.showwarning("Edit Value", "Select a Confidence or Robustness node.")

    def edit_gate_type(self):
        if self.selected_node and self.selected_node.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
            new_gt = simpledialog.askstring("Edit Gate Type", "Enter new gate type (AND/OR):", initialvalue=self.selected_node.gate_type)
            if new_gt is not None and new_gt.upper() in ["AND", "OR"]:
                self.selected_node.gate_type = new_gt.upper()
                self.update_views()
            else:
                messagebox.showerror("Error", "Gate type must be AND or OR.")
        else:
            messagebox.showwarning("Edit Gate Type", "Select a gate-type node.")

    def edit_severity(self):
        if self.selected_node and self.selected_node.node_type.upper() == "TOP EVENT":
            try:
                new_sev = simpledialog.askfloat("Edit Severity", "Enter new severity (1-5):", initialvalue=self.selected_node.severity)
                if new_sev is not None and 1 <= new_sev <= 5:
                    self.selected_node.severity = new_sev
                    self.update_views()
                else:
                    messagebox.showerror("Error", "Severity must be between 1 and 5.")
            except Exception:
                messagebox.showerror("Error", "Invalid input.")
        else:
            messagebox.showwarning("Edit Severity", "Select a Top Event node.")

    def edit_controllability(self):
        if self.selected_node and self.selected_node.node_type.upper() == "TOP EVENT":
            try:
                new_c = simpledialog.askfloat("Edit Controllability", "Enter new controllability (1-5):", initialvalue=self.selected_node.controllability)
                if new_c is not None and 1 <= new_c <= 5:
                    self.selected_node.controllability = new_c
                    self.update_views()
                else:
                    messagebox.showerror("Error", "Controllability must be between 1 and 5.")
            except Exception:
                messagebox.showerror("Error", "Invalid input.")
        else:
            messagebox.showwarning("Edit Controllability", "Select a Top Event node.")

    def edit_page_flag(self):
        if not self.selected_node:
            messagebox.showwarning("Edit Page Flag", "Select a node first.")
            return
        # If this is a clone, update its original.
        target = self.selected_node if self.selected_node.is_primary_instance else self.selected_node.original

        if target.node_type.upper() in ["TOP EVENT", "BASIC EVENT"]:
            messagebox.showwarning("Edit Page Flag", "This node type cannot be a page.")
            return

        # Ask for the new page flag value.
        response = messagebox.askyesno("Edit Page Flag", f"Should node '{target.name}' be a page gate?")
        target.is_page = response

        # Sync the changes to all clones.
        self.sync_nodes_by_id(target)
        self.update_views()

    def set_last_saved_state(self):
        """Record the current model state for change detection."""
        self.last_saved_state = json.dumps(self.export_model_data(), sort_keys=True)

    def has_unsaved_changes(self):
        """Return True if the model differs from the last saved state."""
        current_state = json.dumps(self.export_model_data(), sort_keys=True)
        return current_state != getattr(self, "last_saved_state", None)

    def confirm_close(self):
        """Prompt to save if there are unsaved changes before closing."""
        if self.has_unsaved_changes():
            result = messagebox.askyesnocancel("Unsaved Changes", "Save changes before exiting?")
            if result is None:
                return
            if result:
                self.save_model()
        self.root.destroy()

    def export_model_data(self, include_versions=True):
        reviews = []
        for r in self.reviews:
            reviews.append({
                "name": r.name,
                "description": r.description,
                "mode": r.mode,
                "moderator": r.moderator,
                "approved": r.approved,
                "participants": [asdict(p) for p in r.participants],
                "comments": [asdict(c) for c in r.comments],
            })
        current_name = self.review_data.name if self.review_data else None
        data = {
            "top_events": [event.to_dict() for event in self.top_events],
            "fmeas": [{"name": f['name'], "file": f['file'], "entries": [e.to_dict() for e in f['entries']]} for f in self.fmeas],
            "project_properties": self.project_properties,
            "global_requirements": global_requirements,
            "reviews": reviews,
            "current_review": current_name,
        }
        if include_versions:
            data["versions"] = self.versions
        return data

    def save_model(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            for fmea in self.fmeas:
                self.export_fmea_to_csv(fmea, fmea['file'])
            data = self.export_model_data()
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Saved", "Model saved with all configuration and safety goal information.")
            self.set_last_saved_state()

    def load_model(self):
        global AD_RiskAssessment_Helper
        # Reinitialize the helper so that the counter is reset.
        AD_RiskAssessment_Helper = ADRiskAssessmentHelper()
        
        path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        with open(path, "r") as f:
            raw = f.read()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            import re

            def clean(text: str) -> str:
                text = re.sub(r"//.*", "", text)
                text = re.sub(r"#.*", "", text)
                text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
                text = re.sub(r",\s*(\]|\})", r"\1", text)
                return text

            try:
                data = json.loads(clean(raw))
            except json.JSONDecodeError:
                messagebox.showerror(
                    "Load Model",
                    f"Failed to parse JSON file:\n{exc}",
                )
                return

        if "top_events" in data:
            self.top_events = [FaultTreeNode.from_dict(e) for e in data["top_events"]]
        elif "root_node" in data:
            root = FaultTreeNode.from_dict(data["root_node"])
            self.top_events = [root]
        else:
            messagebox.showerror("Error", "Invalid model file format.")
            return

        self.fmeas = []
        for fmea_data in data.get("fmeas", []):
            entries = [FaultTreeNode.from_dict(e) for e in fmea_data.get("entries", [])]
            self.fmeas.append({"name": fmea_data.get("name", "FMEA"), "file": fmea_data.get("file", f"fmea_{len(self.fmeas)}.csv"), "entries": entries})
        if not self.fmeas and "fmea_entries" in data:
            entries = [FaultTreeNode.from_dict(e) for e in data.get("fmea_entries", [])]
            self.fmeas.append({"name": "Default FMEA", "file": "fmea_default.csv", "entries": entries})

        # Fix clone references for each top event.
        for event in self.top_events:
            AD_RiskAssessment_Helper.fix_clone_references(self.top_events)

        # Update the unique ID counter.
        AD_RiskAssessment_Helper.update_unique_id_counter_for_top_events(self.top_events)
        
        # *** Add this loop to update your global_requirements database ***
        for event in self.top_events:
            self.update_global_requirements_from_nodes(event)
        
        # Load project properties.
        self.project_properties = data.get("project_properties", self.project_properties)
        self.reviews = []
        reviews_data = data.get("reviews")
        if reviews_data:
            for rd in reviews_data:
                participants = [ReviewParticipant(**p) for p in rd.get("participants", [])]
                comments = [ReviewComment(**c) for c in rd.get("comments", [])]
                self.reviews.append(
                    ReviewData(
                        name=rd.get("name", ""),
                        description=rd.get("description", ""),
                        mode=rd.get("mode", "peer"),
                        moderator=rd.get("moderator", ""),
                        participants=participants,
                        comments=comments,
                        approved=rd.get("approved", False),
                    )
                )
            current = data.get("current_review")
            self.review_data = None
            for r in self.reviews:
                if r.name == current:
                    self.review_data = r
                    break
        else:
            rd = data.get("review_data")
            if rd:
                participants = [ReviewParticipant(**p) for p in rd.get("participants", [])]
                comments = [ReviewComment(**c) for c in rd.get("comments", [])]
                review = ReviewData(
                    name=rd.get("name", "Review 1"),
                    description=rd.get("description", ""),
                    mode=rd.get("mode", "peer"),
                    moderator=rd.get("moderator", ""),
                    participants=participants,
                    comments=comments,
                    approved=rd.get("approved", False),
                )
                self.reviews = [review]
                self.review_data = review
            else:
                self.review_data = None
        self.versions = data.get("versions", [])

        self.selected_node = None
        if hasattr(self, "page_diagram") and self.page_diagram is not None:
            self.close_page_diagram()
        self.update_views()
        self.set_last_saved_state()
        
    def update_global_requirements_from_nodes(self,node):
        if hasattr(node, "safety_requirements"):
            for req in node.safety_requirements:
                # Use req["id"] as key; if already exists, you could update if needed.
                if req["id"] not in global_requirements:
                    global_requirements[req["id"]] = req
        for child in node.children:
            self.update_global_requirements_from_nodes(child)

    def generate_report(self):
        path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML", "*.html")])
        if path:
            html = self.build_html_report()
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            messagebox.showinfo("Report", "HTML report generated.")

    def build_html_report(self):
        def node_to_html(n):
            txt = f"{n.name} ({n.node_type}"
            if n.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
                txt += f", {n.gate_type}"
            txt += ")"
            if n.display_label:
                txt += f" => {n.display_label}"
            if n.description:
                txt += f"<br>Desc: {n.description}"
            if n.rationale:
                txt += f"<br>Rationale: {n.rationale}"
            content = f"<details open><summary>{txt}</summary>\n"
            for c in n.children:
                content += node_to_html(c)
            content += "</details>\n"
            return content
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Autonomous Driving Risk Assessment</title>
<style>body {{ font-family: Arial; }} details {{ margin-left: 20px; }}</style>
</head>
<body>
<h1>Autonomous Driving Risk Assessment</h1>
{node_to_html(self.root_node)}
</body>
</html>"""
    def resolve_original(self,node):
        # Walk the clone chain until you find a primary instance.
        while not node.is_primary_instance and node.original is not None and node.original != node:
            node = node.original
        return node

    def open_page_diagram(self, node, push_history=True):
        # Resolve the node to its original.
        resolved_node = self.resolve_original(node)
        if push_history and hasattr(self, "page_diagram") and self.page_diagram is not None:
            self.page_history.append(self.page_diagram.root_node)
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        # Create header frame with the original node’s name.
        header_frame = ttk.Frame(self.canvas_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)

        header = tk.Label(header_frame, text=f"Page Diagram: {resolved_node.name}",
                          font=("Arial", 14, "bold"))
        header.grid(row=0, column=0, sticky="w", padx=(5, 0))
        back_button = ttk.Button(header_frame, text="Go Back", command=self.go_back)
        back_button.grid(row=0, column=1, sticky="e", padx=5)

        page_canvas = tk.Canvas(self.canvas_frame, bg="white")
        page_canvas.grid(row=1, column=0, sticky="nsew")
        vbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=page_canvas.yview)
        vbar.grid(row=1, column=1, sticky="ns")
        self.canvas_frame.rowconfigure(0, weight=0)
        self.canvas_frame.rowconfigure(1, weight=1)
        self.canvas_frame.columnconfigure(0, weight=1)

        # Use the resolved (original) node for the page diagram.
        self.page_diagram = PageDiagram(self, resolved_node, page_canvas)
        self.page_diagram.redraw_canvas()

    def go_back(self):
        if self.page_history:
            # Pop one page off the history and open it without pushing the current page again.
            previous_page = self.page_history.pop()
            self.open_page_diagram(previous_page, push_history=False)
        #else:
            # If history is empty, remain on the current (root) page.
            #messagebox.showinfo("Back", "You are already at the root page.")

    def draw_page_subtree(self, page_root):
        self.page_canvas.delete("all")
        self.draw_page_grid()
        visited_ids = set()
        self.draw_page_connections_subtree(page_root, visited_ids)
        self.draw_page_nodes_subtree(page_root)
        bbox = self.page_canvas.bbox("all")
        if bbox:
            self.page_canvas.config(scrollregion=bbox)

    def draw_page_grid(self):
        spacing = 20
        width = self.page_canvas.winfo_width() or 800
        height = self.page_canvas.winfo_height() or 600
        for x in range(0, width, spacing):
            self.page_canvas.create_line(x, 0, x, height, fill="#ddd", tags="grid")
        for y in range(0, height, spacing):
            self.page_canvas.create_line(0, y, width, y, fill="#ddd", tags="grid")

    def draw_page_connections_subtree(self, node, visited_ids):
        if id(node) in visited_ids:
            return
        visited_ids.add(id(node))
        region_width = 100
        parent_bottom = (node.x, node.y + 40)
        N = len(node.children)
        for i, child in enumerate(node.children):
            parent_conn = (node.x - region_width/2 + (i+0.5)*(region_width/N), parent_bottom[1])
            child_top = (child.x, child.y - 45)
            draw_90_connection(self.page_canvas, parent_conn, child_top, outline_color="dimgray", line_width=1)
        for child in node.children:
            self.draw_page_connections_subtree(child, visited_ids)

    def draw_page_nodes_subtree(self, node):
        self.draw_node_on_page_canvas(node)
        for child in node.children:
            self.draw_page_nodes_subtree(child)

    def draw_node_on_page_canvas(self, canvas, node):
        # Use the clone's own display label and append a marker
        if not node.is_primary_instance:
            display_label = node.display_label + " (clone)"
        else:
            display_label = node.display_label
        
        fill_color = self.get_node_fill_color(node)
        eff_x, eff_y = node.x, node.y
        top_text = f"Type: {node.node_type}"
        if node.input_subtype:
            top_text += f" ({node.input_subtype})"
        if node.description:
            top_text += f"\nDesc: {node.description}"
        if node.rationale:
            top_text += f"\nRationale: {node.rationale}"
        bottom_text = node.name
        
        # For page elements, assume they use a triangle shape.
        if node.is_page:
            # If it’s a clone, you might choose to draw with a different outline (e.g. red or dashed)
            if not node.is_primary_instance:
                fta_drawing_helper.draw_triangle_shape(canvas, eff_x, eff_y, scale=40,
                                                       top_text=top_text,
                                                       bottom_text=bottom_text,
                                                       fill=fill_color,
                                                       outline_color="red",  # mark clone with red outline
                                                       line_width=1,
                                                       font_obj=self.diagram_font)
            else:
                fta_drawing_helper.draw_triangle_shape(canvas, eff_x, eff_y, scale=40,
                                                       top_text=top_text,
                                                       bottom_text=bottom_text,
                                                       fill=fill_color,
                                                       outline_color="dimgray",
                                                       line_width=1,
                                                       font_obj=self.diagram_font)
        else:
            node_type_upper = node.node_type.upper()
            if node_type_upper in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
                if node.gate_type and node.gate_type.upper() == "OR":
                    fta_drawing_helper.draw_rotated_or_gate_shape(self.page_canvas, eff_x, eff_y,
                                               scale=40,
                                               top_text=top_text,
                                               bottom_text=bottom_text,
                                               fill=fill_color,
                                               outline_color="dimgray",
                                               line_width=1)
                else:
                    fta_drawing_helper.draw_rotated_and_gate_shape(self.page_canvas, eff_x, eff_y,
                                                scale=40,
                                                top_text=top_text,
                                                bottom_text=bottom_text,
                                                fill=fill_color,
                                                outline_color="dimgray",
                                                line_width=1)
            elif node_type_upper in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
                fta_drawing_helper.draw_circle_event_shape(self.page_canvas, eff_x, eff_y, 45,
                                        top_text=top_text,
                                        bottom_text=bottom_text,
                                        fill=fill_color,
                                        outline_color="dimgray",
                                        line_width=1)
            else:
                fta_drawing_helper.draw_circle_event_shape(self.page_canvas, eff_x, eff_y, 45,
                                        top_text=top_text,
                                        bottom_text=bottom_text,
                                        fill=fill_color,
                                        outline_color="dimgray",
                                        line_width=1)

        if self.review_data:
            unresolved = any(c.node_id == node.unique_id and not c.resolved for c in self.review_data.comments)
            if unresolved:
                canvas.create_oval(eff_x + 35, eff_y + 35, eff_x + 45, eff_y + 45, fill='yellow', outline='black')

        if self.review_data:
            unresolved = any(c.node_id == node.unique_id and not c.resolved for c in self.review_data.comments)
            if unresolved:
                canvas.create_oval(eff_x + 35, eff_y + 35, eff_x + 45, eff_y + 45, fill='yellow', outline='black')

        if self.review_data:
            unresolved = any(c.node_id == node.unique_id and not c.resolved for c in self.review_data.comments)
            if unresolved:
                canvas.create_oval(eff_x + 35, eff_y + 35, eff_x + 45, eff_y + 45, fill='yellow', outline='black')

        if self.review_data:
            unresolved = any(c.node_id == node.unique_id and not c.resolved for c in self.review_data.comments)
            if unresolved:
                canvas.create_oval(eff_x + 35, eff_y + 35, eff_x + 45, eff_y + 45, fill='yellow', outline='black')

    def on_ctrl_mousewheel_page(self, event):
        if event.delta > 0:
            self.page_diagram.zoom_in()
        else:
            self.page_diagram.zoom_out()

    def close_page_diagram(self):
        if self.page_history:
            prev = self.page_history.pop()
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()
            if prev is None:
                self.canvas = tk.Canvas(self.canvas_frame, bg="white")
                self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                self.hbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
                self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
                self.vbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
                self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
                self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set,
                                   scrollregion=(0, 0, 2000, 2000))
                self.canvas.bind("<ButtonPress-3>", self.on_right_mouse_press)
                self.canvas.bind("<B3-Motion>", self.on_right_mouse_drag)
                self.canvas.bind("<Button-1>", self.on_canvas_click)
                self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
                self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
                self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
                self.canvas.bind("<ButtonRelease-3>", self.show_context_menu)
                self.update_views()
                self.page_diagram = None
            else:
                self.open_page_diagram(prev)
        else:
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()
            self.canvas = tk.Canvas(self.canvas_frame, bg="white")
            self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.hbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
            self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
            self.vbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
            self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set,
                               scrollregion=(0, 0, 2000, 2000))
            self.canvas.bind("<ButtonPress-3>", self.on_right_mouse_press)
            self.canvas.bind("<B3-Motion>", self.on_right_mouse_drag)
            self.canvas.bind("<Button-1>", self.on_canvas_click)
            self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
            self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
            self.canvas.bind("<ButtonRelease-3>", self.show_context_menu)
            self.update_views()
            self.page_diagram = None

    # --- Review Toolbox Methods ---
    def start_peer_review(self):
        dialog = ParticipantDialog(self.root, joint=False)

        if dialog.result:
            parts = dialog.result
            moderator = dialog.moderator
            name = simpledialog.askstring("Review Name", "Enter unique review name:")
            if not name:
                return
            if not moderator:
                messagebox.showerror("Review", "Please specify a moderator")
                return
            if any(r.name == name for r in self.reviews):
                messagebox.showerror("Review", "Name already exists")
                return
            scope = ReviewScopeDialog(self.root, self)
            fta_ids, fmea_names = scope.result if scope.result else ([], [])
            review = ReviewData(name=name, mode='peer', moderator=moderator,
                               participants=parts, comments=[],
                               fta_ids=fta_ids, fmea_names=fmea_names)
            self.reviews.append(review)
            self.review_data = review
            self.current_user = parts[0].name
            ReviewDocumentDialog(self.root, self, review)
            self.open_review_toolbox()

    def start_joint_review(self):
        dialog = ParticipantDialog(self.root, joint=True)
        if dialog.result:
            participants = dialog.result
            moderator = dialog.moderator
            name = simpledialog.askstring("Review Name", "Enter unique review name:")
            if not name:
                return
            if not moderator:
                messagebox.showerror("Review", "Please specify a moderator")
                return
            if any(r.name == name for r in self.reviews):
                messagebox.showerror("Review", "Name already exists")
                return
            scope = ReviewScopeDialog(self.root, self)
            fta_ids, fmea_names = scope.result if scope.result else ([], [])
            review = ReviewData(name=name, mode='joint', moderator=moderator,
                               participants=participants, comments=[],
                               fta_ids=fta_ids, fmea_names=fmea_names)
            self.reviews.append(review)
            self.review_data = review
            self.current_user = participants[0].name
            ReviewDocumentDialog(self.root, self, review)
            self.open_review_toolbox()

    def open_review_toolbox(self):
        if not self.reviews:
            messagebox.showwarning("Review", "No reviews defined")
            return
        if not self.review_data and self.reviews:
            self.review_data = self.reviews[0]
        if self.review_window is None or not self.review_window.winfo_exists():
            self.review_window = ReviewToolbox(self.root, self)
        self.set_current_user()

    def add_version(self):
        name = f"v{len(self.versions)+1}"
        # Exclude the versions list when capturing a snapshot to avoid
        # recursively embedding previous versions within each saved state.
        data = self.export_model_data(include_versions=False)
        self.versions.append({"name": name, "data": data})

    def compare_versions(self):
        if not self.versions:
            messagebox.showinfo("Versions", "No previous versions")
            return
        VersionCompareDialog(self.root, self)

    def merge_review_comments(self):
        path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        with open(path, "r") as f:
            data = json.load(f)

        for rd in data.get("reviews", []):
            participants = [ReviewParticipant(**p) for p in rd.get("participants", [])]
            comments = [ReviewComment(**c) for c in rd.get("comments", [])]
            review = next((r for r in self.reviews if r.name == rd.get("name", "")), None)
            if review is None:
                review = ReviewData(
                    name=rd.get("name", ""),
                    description=rd.get("description", ""),
                    mode=rd.get("mode", "peer"),
                    moderator=rd.get("moderator", ""),
                    participants=participants,
                    comments=comments,
                    approved=rd.get("approved", False),
                    fta_ids=rd.get("fta_ids", []),
                    fmea_names=rd.get("fmea_names", []),
                )
                self.reviews.append(review)
                continue
            for p in participants:
                if all(p.name != ep.name for ep in review.participants):
                    review.participants.append(p)
            next_id = len(review.comments) + 1
            for c in comments:
                review.comments.append(ReviewComment(next_id, c.node_id, c.text, c.reviewer,
                                                     target_type=c.target_type, req_id=c.req_id,
                                                     field=c.field, resolved=c.resolved,
                                                     resolution=c.resolution))
                next_id += 1
        messagebox.showinfo("Merge", "Comments merged")

    def calculate_diff_nodes(self, old_data):
        old_map = self.node_map_from_data(old_data["top_events"])
        new_map = self.node_map_from_data([e.to_dict() for e in self.top_events])
        changed = []
        for nid, nd in new_map.items():
            if nid not in old_map:
                changed.append(nid)
            elif json.dumps(old_map[nid], sort_keys=True) != json.dumps(nd, sort_keys=True):
                changed.append(nid)
        return changed

    def calculate_diff_between(self, data1, data2):
        map1 = self.node_map_from_data(data1["top_events"])
        map2 = self.node_map_from_data(data2["top_events"])
        changed = []
        for nid, nd in map2.items():
            if nid not in map1 or json.dumps(map1.get(nid, {}), sort_keys=True) != json.dumps(nd, sort_keys=True):
                changed.append(nid)
        return changed

    def node_map_from_data(self, top_events):
        result = {}
        def visit(d):
            result[d["unique_id"]] = d
            for ch in d.get("children", []):
                visit(ch)
        for t in top_events:
            visit(t)
        return result

    def set_current_user(self):
        if not self.review_data:
            messagebox.showwarning("User", "Start a review first")
            return
        allowed = [p.name for p in self.review_data.participants]
        if self.review_data.moderator:
            allowed.append(self.review_data.moderator)
        name = simpledialog.askstring("Current User", "Enter your name:", initialvalue=self.current_user)
        if not name:
            return
        if name not in allowed:
            messagebox.showerror("User", "Name not found in participants")
            return
        self.current_user = name

    def get_current_user_role(self):
        if not self.review_data:
            return None
        if self.current_user == self.review_data.moderator:
            return "moderator"
        for p in self.review_data.participants:
            if p.name == self.current_user:
                return p.role
        return None

    def focus_on_node(self, node):
        self.selected_node = node
        try:
            if hasattr(self, "canvas") and self.canvas.winfo_exists():
                self.redraw_canvas()
                bbox = self.canvas.bbox("all")
                if bbox:
                    self.canvas.xview_moveto(max(0, (node.x * self.zoom - self.canvas.winfo_width()/2) / bbox[2]))
                    self.canvas.yview_moveto(max(0, (node.y * self.zoom - self.canvas.winfo_height()/2) / bbox[3]))
        except tk.TclError:
            pass

    def get_review_targets(self):
        targets = []
        target_map = {}

        # Determine which FTAs and FMEAs are part of the current review.
        if self.review_data:
            allowed_ftas = set(self.review_data.fta_ids)
            allowed_fmeas = set(self.review_data.fmea_names)
        else:
            allowed_ftas = set()
            allowed_fmeas = set()

        # Collect nodes from the selected FTAs (or all if none selected).
        nodes = []
        if allowed_ftas:
            for te in self.top_events:
                if te.unique_id in allowed_ftas:
                    nodes.extend(self.get_all_nodes(te))
        else:
            nodes = self.get_all_nodes_in_model()

        # Determine which nodes have FMEA entries in the selected FMEAs.
        fmea_node_ids = set()
        if allowed_fmeas:
            for fmea in self.fmeas:
                if fmea["name"] in allowed_fmeas:
                    fmea_node_ids.update(be.unique_id for be in fmea["entries"])
        else:
            # When no FMEA was selected, do not offer FMEA-related targets
            fmea_node_ids = set()

        for node in nodes:
            label = node.user_name or node.description or f"Node {node.unique_id}"
            targets.append(label)
            target_map[label] = ("node", node.unique_id)
            if hasattr(node, "safety_requirements"):
                for req in node.safety_requirements:
                    rlabel = f"{label} [Req {req.get('id')}]"
                    targets.append(rlabel)
                    target_map[rlabel] = ("requirement", node.unique_id, req.get("id"))

            if node.node_type.upper() == "BASIC EVENT" and node.unique_id in fmea_node_ids:
                flabel = f"{label} [FMEA]"
                targets.append(flabel)
                target_map[flabel] = ("fmea", node.unique_id)
                for field in ["Failure Mode", "Effect", "Cause", "Severity", "Occurrence", "Detection", "RPN"]:
                    slabel = f"{label} [FMEA {field}]"
                    key = field.lower().replace(' ', '_')
                    target_map[slabel] = ("fmea_field", node.unique_id, key)
                    targets.append(slabel)

        return targets, target_map

##########################################
# Node Model 
##########################################
class FaultTreeNode:
    def __init__(self, user_name, node_type, parent=None):
        self.unique_id = AD_RiskAssessment_Helper.get_next_unique_id()
        self.user_name = user_name
        self.node_type = node_type
        self.children = []
        self.parents = []
        if parent is not None:
            self.parents.append(parent)
        self.quant_value = None
        self.gate_type = "AND" if node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"] else None
        self.description = ""
        self.rationale = ""
        self.x = 50
        self.y = 50
        self.severity = 5 if node_type.upper() == "TOP EVENT" else None
        self.controllability = 3 if node_type.upper() == "TOP EVENT" else None
        self.input_subtype = None
        self.display_label = ""
        self.equation = ""
        self.detailed_equation = ""
        self.is_page = False
        self.is_primary_instance = True
        self.original = self
        self.safety_goal_description = ""
        self.safety_goal_asil = ""
        self.vehicle_safety_requirements = []          # List of vehicle safety requirements
        self.operational_safety_requirements = []        # List of operational safety requirements
        # Each requirement is a dict with keys: "id", "req_type" and "text"
        self.safety_requirements = []
        # --- FMEA attributes for basic events (AIAG style) ---
        self.fmea_effect = ""       # Description of effect/failure mode
        self.fmea_cause = ""        # Potential cause of failure
        self.fmea_severity = 1       # 1-10 scale
        self.fmea_occurrence = 1     # 1-10 scale
        self.fmea_detection = 1      # 1-10 scale
        self.fmea_component = ""     # Optional component name for FMEA-only nodes
        # Probability values for classical FTA calculations
        self.failure_prob = 0.0
        self.probability = 0.0

    @property
    def name(self):
        orig = getattr(self, "original", self)
        if not self.is_primary_instance:
            return f"Node {orig.unique_id}: {self.user_name}" if self.user_name else f"Node {orig.unique_id}"
        else:
            return f"Node {self.unique_id}: {self.user_name}" if self.user_name else f"Node {self.unique_id}"

    def to_dict(self):
        d = {
            "unique_id": self.unique_id,
            "user_name": self.user_name,
            "type": self.node_type,
            "quant_value": self.quant_value,
            "gate_type": self.gate_type,
            "description": self.description,
            "rationale": self.rationale,
            "x": self.x,
            "y": self.y,
            "severity": self.severity,
            "controllability": self.controllability,
            "input_subtype": self.input_subtype,
            "is_page": self.is_page,
            "is_primary_instance": self.is_primary_instance,
            "safety_goal_description": self.safety_goal_description,
            "safety_goal_asil": self.safety_goal_asil,
            "fmea_effect": self.fmea_effect,
            "fmea_cause": self.fmea_cause,
            "fmea_severity": self.fmea_severity,
            "fmea_occurrence": self.fmea_occurrence,
            "fmea_detection": self.fmea_detection,
            "fmea_component": self.fmea_component,
            # Save the safety requirements list (which now includes custom_id)
            "safety_requirements": self.safety_requirements,
            "failure_prob": self.failure_prob,
            "probability": self.probability,
            "children": [child.to_dict() for child in self.children]
        }
        if not self.is_primary_instance and self.original and (self.original.unique_id != self.unique_id):
            d["original_id"] = self.original.unique_id
        return d

    @staticmethod
    def from_dict(data, parent=None):
        node = FaultTreeNode.__new__(FaultTreeNode)
        node.user_name = data.get("user_name", "")
        node.node_type = data.get("type", "")
        node.children = [FaultTreeNode.from_dict(child_data, parent=node) for child_data in data.get("children", [])]
        node.parents = []
        if parent is not None:
            node.parents.append(parent)
        node.quant_value = data.get("quant_value")
        node.gate_type = data.get("gate_type", "AND")
        node.description = data.get("description", "")
        node.rationale = data.get("rationale", "")
        node.x = data.get("x", 50)
        node.y = data.get("y", 50)
        node.severity = data.get("severity", 5) if node.node_type.upper() == "TOP EVENT" else None
        node.controllability = data.get("controllability", 3) if node.node_type.upper() == "TOP EVENT" else None
        node.input_subtype = data.get("input_subtype", None)
        node.is_page = boolify(data.get("is_page", False), False)
        node.is_primary_instance = boolify(data.get("is_primary_instance", True), True)
        node.safety_goal_description = data.get("safety_goal_description", "")
        node.safety_goal_asil = data.get("safety_goal_asil", "")
        node.fmea_effect = data.get("fmea_effect", "")
        node.fmea_cause = data.get("fmea_cause", "")
        node.fmea_severity = data.get("fmea_severity", 1)
        node.fmea_occurrence = data.get("fmea_occurrence", 1)
        node.fmea_detection = data.get("fmea_detection", 1)
        node.fmea_component = data.get("fmea_component", "")
        # NEW: Load safety_requirements (or default to empty list)
        node.safety_requirements = data.get("safety_requirements", [])
        node.failure_prob = data.get("failure_prob", 0.0)
        node.probability = data.get("probability", 0.0)
        node.display_label = ""
        node.equation = ""
        node.detailed_equation = ""
        if "unique_id" in data:
            node.unique_id = data["unique_id"]
        else:
            node.unique_id = AD_RiskAssessment_Helper.get_next_unique_id()
        if not node.is_primary_instance and "original_id" in data:
            node._original_id = data["original_id"]
        else:
            node._original_id = None
        return node
        
##########################################
# Page Diagram 
##########################################
class PageDiagram:
    def __init__(self, app, page_gate_node, canvas):
        self.app = app
        self.root_node = page_gate_node
        self.canvas = canvas
        self.zoom = 1.0
        self.diagram_font = tkFont.Font(family="Arial", size=int(8 * self.zoom))
        self.grid_size = 20
        self.selected_node = None
        self.dragging_node = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.rc_dragged = False

        # Bind events – including right-click release
        self.canvas.bind("<ButtonPress-3>", self.on_right_mouse_press)
        self.canvas.bind("<B3-Motion>", self.on_right_mouse_drag)
        self.canvas.bind("<ButtonRelease-3>", self.on_right_mouse_release)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_mousewheel)

    def on_right_mouse_press(self, event):
        self.rc_dragged = False
        self.canvas.scan_mark(event.x, event.y)

    def on_right_mouse_drag(self, event):
        self.rc_dragged = True
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_right_mouse_release(self, event):
        # If there was no significant drag, show the context menu.
        if not self.rc_dragged:
            self.show_context_menu(event)

    def find_node_at_position(self, x, y):
        # Adjust the radius (here using 45 as an example)
        radius_sq = (45 * self.zoom) ** 2
        for n in self.get_all_nodes(self.root_node):
            if (x - n.x) ** 2 + (y - n.y) ** 2 < radius_sq:
                return n
        return None
        
    def on_ctrl_mousewheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
            
    def get_all_nodes(self, node=None):
        if node is None:
            node = self.root_node
        visited = set()

        def rec(n):
            if n.unique_id in visited:
                return []
            visited.add(n.unique_id)

            # Skip nodes if a parent is page, but that page is NOT our root_node
            if n != self.root_node and any(p.is_page and p != self.root_node for p in n.parents):
                return []

            result = [n]
            for c in n.children:
                result.extend(rec(c))
            return result

        return rec(node)

    def rc_on_press(self, event):
        self.rc_start = (event.x, event.y)
        self.rc_dragged = False
        self.canvas.scan_mark(event.x, event.y)

    def rc_on_motion(self, event):
        self.rc_dragged = True
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def rc_on_release(self, event):
        if not self.rc_dragged:
            self.show_context_menu(event)

    def show_context_menu(self, event):
        x = self.canvas.canvasx(event.x) / self.zoom
        y = self.canvas.canvasy(event.y) / self.zoom
        node = None
        for n in self.get_all_nodes(self.root_node):
            radius = 60 if n.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"] else 45
            if (x - n.x)**2 + (y - n.y)**2 < radius**2:
                node = n
                break
        if not node:
            return
        self.selected_node = node
        self.app.selected_node = node
        menu = tk.Menu(self.app.root, tearoff=0)
        menu.add_command(label="Edit", command=lambda: self.context_edit(node))
        menu.add_command(label="Remove Connection", command=lambda: self.context_remove(node))
        menu.add_command(label="Delete Node", command=lambda: self.context_delete(node))
        menu.add_command(label="Copy", command=lambda: self.context_copy(node))
        menu.add_command(label="Cut", command=lambda: self.context_cut(node))
        menu.add_command(label="Paste", command=lambda: self.context_paste(node))
        if node.node_type.upper() not in ["TOP EVENT", "BASIC EVENT"]:
            menu.add_command(label="Edit Page Flag", command=lambda: self.context_edit_page_flag(node))
        menu.add_separator()
        menu.add_command(label="Add Confidence", command=lambda: self.context_add("Confidence Level"))
        menu.add_command(label="Add Robustness", command=lambda: self.context_add("Robustness Score"))
        menu.add_command(label="Add Gate", command=lambda: self.context_add("GATE"))
        menu.add_command(label="Add Basic Event", command=lambda: self.context_add("Basic Event"))
        menu.tk_popup(event.x_root, event.y_root)

    def context_edit(self, node):
        EditNodeDialog(self.canvas, node, self.app)
        self.redraw_canvas()
        self.app.update_views()

    def context_remove(self, node):
        self.selected_node = node
        self.app.remove_connection(node)
        self.redraw_canvas()
        self.app.update_views()

    def context_delete(self, node):
        self.selected_node = node
        self.app.delete_node_and_subtree(node)
        self.redraw_canvas()
        self.app.update_views()

    def context_copy(self, node):
        self.selected_node = node
        self.app.copy_node()

    def context_cut(self, node):
        self.selected_node = node
        self.app.cut_node()

    def context_paste(self, node):
        self.selected_node = node
        self.app.paste_node()

    def context_edit_page_flag(self, node):
        self.selected_node = node
        self.app.edit_page_flag()
        self.redraw_canvas()

    def context_add(self, event_type):
        self.app.selected_node = self.selected_node
        self.app.add_node_of_type(event_type)
        self.redraw_canvas()
        self.app.update_views()

    def on_canvas_click(self, event):
        x = self.canvas.canvasx(event.x) / self.zoom
        y = self.canvas.canvasy(event.y) / self.zoom
        clicked_node = None
        for n in self.get_all_nodes(self.root_node):
            radius = 60 if n.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"] else 45
            if (x - n.x)**2 + (y - n.y)**2 < radius**2:
                clicked_node = n
                break
        self.selected_node = clicked_node
        self.app.selected_node = clicked_node
        if clicked_node and clicked_node is not self.root_node:
            self.dragging_node = clicked_node
            self.drag_offset_x = x - clicked_node.x
            self.drag_offset_y = y - clicked_node.y
        else:
            self.dragging_node = None
        self.redraw_canvas()
        
    def on_canvas_double_click(self, event):
        x = self.canvas.canvasx(event.x) / self.zoom
        y = self.canvas.canvasy(event.y) / self.zoom
        clicked_node = self.find_node_at_position(x, y)
        if clicked_node:
            if not clicked_node.is_primary_instance:
                self.app.open_page_diagram(getattr(clicked_node, "original", clicked_node))
            else:
                if clicked_node.is_page:
                    self.app.open_page_diagram(clicked_node)
                else:
                    EditNodeDialog(self.app.root, clicked_node, self.app)
            self.app.update_views()

    def on_canvas_drag(self, event):
        if self.dragging_node:
            x = self.canvas.canvasx(event.x) / self.zoom
            y = self.canvas.canvasy(event.y) / self.zoom
            new_x = x - self.drag_offset_x
            new_y = y - self.drag_offset_y
            dx = new_x - self.dragging_node.x
            dy = new_y - self.dragging_node.y
            self.dragging_node.x = new_x
            self.dragging_node.y = new_y
            if self.dragging_node.is_primary_instance:
                self.app.move_subtree(self.dragging_node, dx, dy)
            self.app.sync_nodes_by_id(self.dragging_node)
            self.redraw_canvas()

    def on_canvas_release(self, event):
        if self.dragging_node:
            self.dragging_node.x = round(self.dragging_node.x/self.grid_size)*self.grid_size
            self.dragging_node.y = round(self.dragging_node.y/self.grid_size)*self.grid_size
        self.dragging_node = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0

    def on_canvas_double_click(self, event):
        x = self.canvas.canvasx(event.x) / self.zoom
        y = self.canvas.canvasy(event.y) / self.zoom
        clicked_node = None
        for n in self.get_all_nodes(self.root_node):
            radius = 60 if n.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"] else 45
            if (x - n.x)**2 + (y - n.y)**2 < radius**2:
                clicked_node = n
                break
        if clicked_node:
            if not clicked_node.is_primary_instance:
                self.app.open_page_diagram(getattr(clicked_node, "original", clicked_node))
            else:
                if clicked_node.is_page:
                    self.app.open_page_diagram(clicked_node)
                else:
                    EditNodeDialog(self.app.root, clicked_node, self.app)
            self.app.update_views()

    def zoom_in(self):
        self.zoom *= 1.2
        self.diagram_font.config(size=int(8 * self.zoom))
        self.redraw_canvas()

    def zoom_out(self):
        self.zoom /= 1.2
        self.diagram_font.config(size=int(8 * self.zoom))
        self.redraw_canvas()

    def auto_arrange(self):
        horizontal_gap = 150
        vertical_gap = 100
        next_y = [100]
        def layout(node, depth):
            node.x = depth * horizontal_gap + 100
            if not node.children:
                node.y = next_y[0]
                next_y[0] += vertical_gap
            else:
                for child in node.children:
                    layout(child, depth+1)
                node.y = (node.children[0].y + node.children[-1].y) / 2
        layout(self.root_node, 0)
        self.redraw_canvas()

    def redraw_canvas(self):
        # Clear the canvas and draw the grid first.
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return
        self.canvas.delete("all")
        self.draw_grid()
        
        # Use the page's root node as the sole top-level event.
        drawn_ids = set()
        for top_event in [self.root_node]:
            self.draw_connections(top_event, drawn_ids)
        
        all_nodes = []
        for top_event in [self.root_node]:
            all_nodes.extend(self.get_all_nodes(top_event))
        for node in all_nodes:
            self.draw_node(node)
        
        # Update the scroll region.
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def draw_grid(self):
        spacing = self.grid_size * self.zoom
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width < 10: 
            width = 800
        if height < 10: 
            height = 600
        for x in range(0, int(width), int(spacing)):
            self.canvas.create_line(x, 0, x, height, fill="#ddd", tags="grid")
        for y in range(0, int(height), int(spacing)):
            self.canvas.create_line(0, y, width, y, fill="#ddd", tags="grid")

    def draw_connections(self, node, drawn_ids=set()):
        if id(node) in drawn_ids:
            return
        drawn_ids.add(id(node))
        if node.is_page and node.is_primary_instance and node != self.root_node:
            return
        if node.children:
            region_width = 100 * self.zoom
            parent_bottom = (node.x * self.zoom, node.y * self.zoom + 40 * self.zoom)
            N = len(node.children)
            for i, child in enumerate(node.children):
                parent_conn = (node.x * self.zoom - region_width/2 + (i+0.5)*(region_width/N), parent_bottom[1])
                child_top = (child.x * self.zoom, child.y * self.zoom - 45 * self.zoom)
                fta_drawing_helper.draw_90_connection(self.canvas, parent_conn, child_top, outline_color="dimgray", line_width=1)
            for child in node.children:
                self.draw_connections(child, drawn_ids)

    def draw_node(self, node):
        """
        Draws the given node on the main canvas.
        For clones, it always uses the original’s non-positional attributes (like display_label,
        description, etc.) so that any changes to the original are reflected on all clones.
        """
        # If the node is a clone, use its original for configuration (non-positional attributes)
        source = node if node.is_primary_instance else node.original

        # For display purposes, show the clone marker on the clone's display_label.
        if node.is_primary_instance:
            display_label = source.display_label
        else:
            display_label = source.display_label + " (clone)"

        # Build a short top_text string from the source's attributes.
        subtype_text = source.input_subtype if source.input_subtype else "N/A"
        top_text = (
            f"Type: {source.node_type}\n"
            f"Subtype: {subtype_text}\n"
            f"{display_label}\n"
            f"Desc: {source.description}\n\n"
            f"Rationale: {source.rationale}"
        )
        # For the bottom text, you may choose to display the node's name (which for a clone is
        # usually the same as the original’s name)
        bottom_text = source.name

        # Compute the effective position using the clone’s own (positional) values
        eff_x = node.x * self.zoom
        eff_y = node.y * self.zoom

        # Highlight if selected
        outline_color = "red" if node == self.selected_node else "dimgray"
        line_width = 2 if node == self.selected_node else 1

        # Determine the fill color (this function already uses the original's display_label)
        fill_color = self.app.get_node_fill_color(node)
        font_obj = self.diagram_font

        # For shape selection, use the source’s node type and gate type.
        node_type_upper = source.node_type.upper()

        if not node.is_primary_instance:
            # For clones, draw them in a “clone” style.
            if source.is_page:
                fta_drawing_helper.draw_triangle_clone_shape(self.canvas, eff_x, eff_y, scale=40 * self.zoom,
                                                             top_text=top_text,
                                                             bottom_text=bottom_text,
                                                             fill=fill_color,
                                                             outline_color=outline_color,
                                                             line_width=1,
                                                             font_obj=self.diagram_font)
            elif node_type_upper in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
                if source.gate_type.upper() == "OR":
                    fta_drawing_helper.draw_rotated_or_gate_clone_shape(
                        self.canvas, eff_x, eff_y, scale=40 * self.zoom,
                        top_text=top_text, bottom_text=bottom_text,
                        fill=fill_color, outline_color=outline_color,
                        line_width=line_width, font_obj=font_obj
                    )
                else:
                    fta_drawing_helper.draw_rotated_and_gate_clone_shape(
                        self.canvas, eff_x, eff_y, scale=40 * self.zoom,
                        top_text=top_text, bottom_text=bottom_text,
                        fill=fill_color, outline_color=outline_color,
                        line_width=line_width, font_obj=font_obj
                    )
            elif node_type_upper in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
                fta_drawing_helper.draw_circle_event_shape(
                    self.canvas, eff_x, eff_y, 45 * self.zoom,
                    top_text=top_text, bottom_text=bottom_text,
                    fill=fill_color, outline_color=outline_color,
                    line_width=line_width, font_obj=font_obj
                )
            else:
                fta_drawing_helper.draw_circle_event_shape(
                    self.canvas, eff_x, eff_y, 45 * self.zoom,
                    top_text=top_text, bottom_text=bottom_text,
                    fill=fill_color, outline_color=outline_color,
                    line_width=line_width, font_obj=font_obj
                )
        else:
            # Primary node: use normal drawing routines.
            if node_type_upper in ["TOP EVENT", "GATE", "RIGOR LEVEL"]:
                if source.is_page and source != self.root_node:
                    fta_drawing_helper.draw_triangle_shape(
                        self.canvas, eff_x, eff_y, scale=40 * self.zoom,
                        top_text=top_text, bottom_text=bottom_text,
                        fill=fill_color, outline_color=outline_color,
                        line_width=line_width, font_obj=font_obj
                    )
                else:
                    if source.gate_type.upper() == "OR":
                        fta_drawing_helper.draw_rotated_or_gate_shape(
                            self.canvas, eff_x, eff_y, scale=40 * self.zoom,
                            top_text=top_text, bottom_text=bottom_text,
                            fill=fill_color, outline_color=outline_color,
                            line_width=line_width, font_obj=font_obj
                        )
                    else:
                        fta_drawing_helper.draw_rotated_and_gate_shape(
                            self.canvas, eff_x, eff_y, scale=40 * self.zoom,
                            top_text=top_text, bottom_text=bottom_text,
                            fill=fill_color, outline_color=outline_color,
                            line_width=line_width, font_obj=font_obj
                        )
            elif node_type_upper in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
                fta_drawing_helper.draw_circle_event_shape(
                    self.canvas, eff_x, eff_y, 45 * self.zoom,
                    top_text=top_text, bottom_text=bottom_text,
                    fill=fill_color, outline_color=outline_color,
                    line_width=line_width, font_obj=font_obj
                )
            else:
                fta_drawing_helper.draw_circle_event_shape(
                    self.canvas, eff_x, eff_y, 45 * self.zoom,
                    top_text=top_text, bottom_text=bottom_text,
                    fill=fill_color, outline_color=outline_color,
                    line_width=line_width, font_obj=font_obj
                )

        # Draw any additional text (such as equations) from the source.
        if source.equation:
            self.canvas.create_text(
                eff_x - 80 * self.zoom, eff_y - 15 * self.zoom,
                text=source.equation, anchor="e", fill="gray",
                font=self.diagram_font
            )
        if source.detailed_equation:
            self.canvas.create_text(
                eff_x - 80 * self.zoom, eff_y + 15 * self.zoom,
                text=source.detailed_equation, anchor="e", fill="gray",
                font=self.diagram_font
            )

        # Finally, if the node appears multiple times, draw a shared marker.
        if self.app.occurrence_counts.get(node.unique_id, 0) > 1:
            marker_x = eff_x + 30 * self.zoom
            marker_y = eff_y - 30 * self.zoom
            fta_drawing_helper.draw_shared_marker(self.canvas, marker_x, marker_y, self.zoom)

def main():
    root = tk.Tk()
    # Create a fresh helper each session:
    global AD_RiskAssessment_Helper
    AD_RiskAssessment_Helper = ADRiskAssessmentHelper()
    
    app = FaultTreeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
