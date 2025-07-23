# FreeCTA

This repository contains a graphical fault tree analysis tool. The latest update adds a **Review Toolbox** supporting peer and joint review workflows.

## Review Toolbox

Launch the review features from the **Review** menu:

* **Start Peer Review** – create at least one moderator and one reviewer, then tick the checkboxes for the FTAs and FMEAs you want to include. Each moderator and participant has an associated email address. A due date is requested and once reached the review becomes read‑only unless a moderator extends it. A document window opens showing the selected elements. FTAs are drawn on canvases you can drag and scroll, while FMEAs appear as full tables listing every field so failures can be reviewed line by line. Linked requirements are listed below and any text changes are colored the same way as other differences. Changes to which requirements are allocated to each item are highlighted in blue and red.
* **Start Joint Review** – add participants with reviewer or approver roles and at least one moderator, select the desired FTAs and FMEAs via checkboxes and enter a unique review name and description. Approvers can approve only after all reviewers are done and comments resolved. Moderators may edit the description, due date or participant list later from the toolbox. The document window behaves the same as for peer reviews with draggable FTAs and tabulated FMEAs. Requirement diffs are also shown in this view.
* **Open Review Toolbox** – manage comments. Selecting a comment focuses the related element and shows the text below the list. Use the **Open Document** button to reopen the visualization for the currently selected review. A drop-down at the top lists every saved review with its approval status.
* **Merge Review Comments** – combine feedback from another saved model into the current one so parallel reviews can be consolidated.
* **Compare Versions** – view earlier approved versions. Differences are listed with a short description and small before/after images of changed FTA nodes. Requirement allocations are compared in the diagrams and logs.
* **Set Current User** – choose who you are when adding comments. The toolbox also provides a drop-down selector.
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

## License

This project is licensed under the GNU General Public License version 3. See the [LICENSE](LICENSE) file for details.
