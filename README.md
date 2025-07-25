# AutoSafeguard Analyzer

This repository contains a graphical fault tree analysis tool. The latest update adds a **Review Toolbox** supporting peer and joint review workflows. The explorer pane now includes an **Analyses** tab listing all FMEAs, FMEDAs, HAZOPs, HARAs and architecture diagrams so they can be opened directly. Architecture objects can now be resized either by editing width and height values or by dragging the red handles that appear when an item is selected. Fork and join bars keep a constant thickness so only their length changes.

## Review Toolbox

Launch the review features from the **Review** menu:

* **Start Peer Review** – create at least one moderator and one reviewer, then tick the checkboxes for the FTAs and FMEAs you want to include. Each moderator and participant has an associated email address. A due date is requested and once reached the review becomes read‑only unless a moderator extends it. A document window opens showing the selected elements. FTAs are drawn on canvases you can drag and scroll, while FMEAs appear as full tables listing every field so failures can be reviewed line by line. Linked requirements are listed below and any text changes are colored the same way as other differences. Changes to which requirements are allocated to each item are highlighted in blue and red.
* **Start Joint Review** – add participants with reviewer or approver roles and at least one moderator, select the desired FTAs and FMEAs via checkboxes and enter a unique review name and description. Approvers can approve only after all reviewers are done and comments resolved. Moderators may edit the description, due date or participant list later from the toolbox. The document window behaves the same as for peer reviews with draggable FTAs and tabulated FMEAs. Requirement diffs are also shown in this view.
* **Open Review Toolbox** – manage comments. Selecting a comment focuses the related element and shows the text below the list. Use the **Open Document** button to reopen the visualization for the currently selected review. A drop-down at the top lists every saved review with its approval status.
* **Merge Review Comments** – combine feedback from another saved model into the current one so parallel reviews can be consolidated.
* **Compare Versions** – view earlier approved versions. Differences are listed with a short description and small before/after images of changed FTA nodes. Requirement allocations are compared in the diagrams and logs.
* **Set Current User** – choose who you are when adding comments. The toolbox also provides a drop-down selector.
* **Update Decomposition** – after splitting a requirement into two, select either child and use the new button in the node dialog to pick a different ASIL pair.
* The target selector within the toolbox only lists nodes and FMEA items that were chosen when the review was created, so comments can only be attached to the scoped elements.

Nodes with unresolved comments show a small yellow circle to help locate feedback quickly.
When a review document is opened it automatically compares the current model to the previous approved version. Added elements appear in blue and removed ones in red just like the **Compare Versions** tool, but only for the FTAs and FMEAs included in that review.

When comparing versions, added nodes and connections are drawn in blue while removed ones are drawn in red. Text differences highlight deleted portions in red and new text in blue so changes to descriptions, rationales or FMEA fields stand out. Deleted links between FTA nodes are shown with red connectors.
Requirement lists are compared as well so allocation changes show up alongside description and rationale edits. The Requirements Matrix window now lists every requirement with the nodes and FMEA items where it is allocated and the safety goals traced to each one.

Comments can be attached to FMEA entries and individual requirements. Resolving a comment prompts for a short explanation which is shown with the original text.

Review information (participants, comments, review names, descriptions and approval state) is saved as part of the model file and restored on load.

## Email Setup

When sending review summaries, the application asks for SMTP settings and login details.
If you use Gmail with two-factor authentication enabled, create an **app password**
and enter it instead of your normal account password. Authentication failures will
prompt you to re-enter these settings.

Each summary email embeds PNG images showing the differences between the current
model and the last approved version for the selected FTAs so reviewers can view
the diagrams directly in the message. CSV files containing the FMEA tables are
attached so they can be opened in Excel or another spreadsheet application. Requirement changes with allocations and safety goal traces are listed below the diagrams.

If sending fails with a connection error, the dialog will prompt again so you
can correct the server address or port.

## Mission Profiles and Probability Formulas

The **Reliability** menu lets you define mission profiles describing the on/off
time, temperatures and other conditions for your system.  When a profile is
present its total `TAU` value is used to convert FIT rates into failure
probabilities for each basic event.

In the *Edit Node* dialog for a basic event you can choose how the FIT rate is
interpreted:

* **linear** – probability is calculated as `λ × τ` where `λ` is the FIT value
  expressed as failures per hour and `τ` comes from the selected mission profile.
* **exponential** – uses the exponential model `1 − exp(−λ × τ)`.
* **constant** – probability comes from the basic event's *Failure Probability*
  field and does not use the FIT rate or mission time.

Mission profiles and the selected formula for each basic event are stored in the
JSON model so results remain consistent when reloading the file.

### Component Qualifications

Reliability calculations now take the qualification certificate of each passive
component into account.  When computing FIT rates, a multiplier based on the
certificate (e.g. *AEC‑Q200* or *MIL‑STD‑883*) is applied so qualified parts
yield lower failure rates.  Active components currently use a neutral factor.
Additional datasheet parameters such as diode forward voltage or MOSFET
`RDS(on)` can be entered when configuring components to better document the
parts used in the analysis.

### BOM Integration with SysML Diagrams

Blocks in block diagrams may reference circuits defined in a saved BOM via the
new **circuit** property while parts reference individual components using the
**component** property.  Both element types also provide **fit**,
**qualification** and **failureModes** attributes.  Entering values for these
fields shows them in a *Reliability* compartment for blocks or as additional
lines beneath parts so FIT rates and qualification information remain visible in
the architecture model. When editing a block or part you can now pick from
drop-down lists containing all circuits or components from saved reliability
analyses. Selecting an item automatically fills in its FIT rate, qualification
certificate and any failure modes found in FMEA tables.

### HAZOP Analysis

The **HAZOP Analysis** window lets you list system functions with one or more
associated malfunctions. Each entry records the malfunction guideword
(*No/Not*, *Unintended*, *Excessive*, *Insufficient* or *Reverse*), the related
scenario, driving conditions and hazard, and whether it is safety relevant.
Covered malfunctions may reference other entries as mitigation. When a function
is allocated to an active component in a reliability analysis, its malfunctions
become selectable failure modes in the FMEDA table.

### HARA Analysis

The **HARA Analysis** view builds on the safety relevant malfunctions from one
or more selected HAZOPs. When creating a new HARA you can pick multiple HAZOP
documents; only malfunctions from those selections appear in the table.
Each HARA table contains the following columns:

1. **Malfunction** – combo box listing malfunctions flagged as safety relevant
   in the chosen HAZOP documents.
2. **Hazard** – textual description of the resulting hazard.
3. **Severity** – ISO&nbsp;26262 severity level (1–3).
4. **Severity Rationale** – free text explanation for the chosen severity.
5. **Controllability** – ISO&nbsp;26262 controllability level (1–3).
6. **Controllability Rationale** – free text explanation for the chosen
   controllability.
7. **Exposure** – ISO&nbsp;26262 exposure level (1–4).
8. **Exposure Rationale** – free text explanation for the chosen exposure.
9. **ASIL** – automatically calculated from severity, controllability and
   exposure using the ISO&nbsp;26262 risk graph.
10. **Safety Goal** – combo box listing all defined safety goals in the project.

The calculated ASIL from each row is propagated to the referenced safety goal so
that inherited ASIL levels appear consistently in all analyses and
documentation, including FTA top level events.

The **Hazard Explorer** window lists all hazards from every HARA in a read-only table for quick review or CSV export.

## License

This project is licensed under the GNU General Public License version 3. See the [LICENSE](LICENSE) file for details.
