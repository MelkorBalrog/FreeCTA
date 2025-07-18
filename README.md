# FreeCTA

This repository contains a graphical fault tree analysis tool. The latest update adds a **Review Toolbox** supporting peer and joint review workflows.

## Review Toolbox

Launch the review features from the **Review** menu:

* **Start Peer Review** – create reviewers and begin commenting.
* **Start Joint Review** – add participants with reviewer or approver roles. Approvers can approve only after all reviewers are done and comments resolved.
* **Open Review Toolbox** – manage comments. Selecting a comment focuses the related element and shows the text below the list.
* **Compare Versions** – view earlier approved versions and highlight differences on the diagram.
* **Set Current User** – choose who you are when adding comments. The toolbox also provides a drop-down selector.

Nodes with unresolved comments show a small yellow circle to help locate feedback quickly. Differences between versions are outlined in blue when comparing.

Comments can be attached to FMEA entries and individual requirements. Resolving a comment prompts for a short explanation which is shown with the original text.

Review information (participants, comments, approval state) is saved as part of the model file and restored on load.
