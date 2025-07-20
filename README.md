# FreeCTA

This repository contains a graphical fault tree analysis tool. The latest update adds a **Review Toolbox** supporting peer and joint review workflows.

## Review Toolbox

Launch the review features from the **Review** menu:

* **Start Peer Review** – create reviewers, then tick the checkboxes for the FTAs and FMEAs you want to include. A document window opens showing those elements. FTAs are drawn on canvases you can drag and scroll, while FMEAs appear as full tables listing every field so failures can be reviewed line by line.
* **Start Joint Review** – add participants with reviewer or approver roles, select the desired FTAs and FMEAs via checkboxes and enter a unique review name and description. Approvers can approve only after all reviewers are done and comments resolved. The document window behaves the same as for peer reviews with draggable FTAs and tabulated FMEAs.
* **Open Review Toolbox** – manage comments. Selecting a comment focuses the related element and shows the text below the list. Use the **Open Document** button to reopen the visualization for the currently selected review. A drop-down at the top lists every saved review with its approval status.
* **Merge Review Comments** – combine feedback from another saved model into the current one so parallel reviews can be consolidated.
* **Compare Versions** – view earlier approved versions. Differences are listed with a short description and small before/after images of changed FTA nodes.
* **Set Current User** – choose who you are when adding comments. The toolbox also provides a drop-down selector.
* The target selector within the toolbox only lists nodes and FMEA items that were chosen when the review was created, so comments can only be attached to the scoped elements.

Nodes with unresolved comments show a small yellow circle to help locate feedback quickly.

When comparing versions, added nodes and connections are drawn in blue while removed ones are drawn in red. Text differences highlight deleted portions in red and new text in blue so changes to descriptions, rationales or FMEA fields stand out. Deleted links between FTA nodes are shown with red connectors.

Comments can be attached to FMEA entries and individual requirements. Resolving a comment prompts for a short explanation which is shown with the original text.

Review information (participants, comments, review names, descriptions and approval state) is saved as part of the model file and restored on load.

## License

This project is licensed under the GNU General Public License version 3. See the [LICENSE](LICENSE) file for details.
