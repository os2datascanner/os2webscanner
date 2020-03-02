## What does this MR do?
<!--
Briefly describe what this MR is about.
Examples:
 Adds new document type: MyNewDocumentType
 Fixes js error in <some functionality>
-->


## Author's checklist
<!--
MRs must be marked as WIP until all checkboxes have been filled.
Checkboxes can be pre-filled before submitting the MR by replacing
[ ] with [x],
-->
- [ ] The code has been rebased/squashed into a minimal amount of atomic commits that reference the ticket ID (eg. `[#12345] Implement featureX in Y`)
- [ ] The title of this MR contains the relevant ticket no., formatted like `[#12345]` or `#12345`
- [ ] The corresponding Redmine ticket has been set to `Needs review` or `Release Management: QA (Int)` (whichever is applicable)
- [ ] The feature/bugfix has been approved by KU or tested manually
- [ ] I have added unit tests or made a conscious decision not to
- [ ] The MR does not introduce indentation or charset issues
- [ ] The code contains inline and/or POD documentation where relevant
- [ ] The feature/bugfix has no dependencies (eg. database/config changes), or: I have noted the dependencies on the corresponding Redmine ticket
- [ ] The feature/bugfix does not depend on changes in `obvius`, or: I have referenced the relevant MR in the description

## Review checklist

- [ ] The code is understandable, well-structured and sufficiently documented
- [ ] I would be able to deploy this feature and verify that it's working without further input from the author
- [ ] I have checked out the code and tested locally, tested the changes on cmstest01.ku.dk or thorougly vetted the code
