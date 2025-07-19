# FreeCTA

This repository contains a graphical fault tree analysis tool. The latest update adds a **Review Toolbox** supporting peer and joint review workflows.

## Review Toolbox

Launch the review features from the **Review** menu:

* **Start Peer Review** – create reviewers, choose which FTAs and FMEAs to review and give the review a unique name and optional description. Hold **Ctrl** to select multiple items. A document window opens showing the chosen FTAs and FMEAs graphically so comments can be added immediately.
* **Start Joint Review** – add participants with reviewer or approver roles, select the elements to be reviewed (use **Ctrl** for multiple selection) and enter a unique review name and description. Approvers can approve only after all reviewers are done and comments resolved.
* **Open Review Toolbox** – manage comments. Selecting a comment focuses the related element and shows the text below the list. A drop-down at the top lists every saved review with its approval status.
* **Merge Review Comments** – combine feedback from another saved model into the current one so parallel reviews can be consolidated.
* **Compare Versions** – view earlier approved versions and highlight differences on the diagram.
* **Set Current User** – choose who you are when adding comments. The toolbox also provides a drop-down selector.

Nodes with unresolved comments show a small yellow circle to help locate feedback quickly. Differences between versions are outlined in blue when comparing.

Comments can be attached to FMEA entries and individual requirements. Resolving a comment prompts for a short explanation which is shown with the original text.

Review information (participants, comments, review names, descriptions and approval state) is saved as part of the model file and restored on load.
