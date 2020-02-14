OS2datascanner
==============

Version 3.1.0, 14th February 2020
---------------------------------

"Plug and Play"

New in this version:

- SAML support in the report module:

  - Users can now log in to the report module with organisational SSO.

  - Metadata provided by SAML identity providers can be used to relate users to
    matches.

- Initial support for scanning Exchange Web Services servers.

- The interface of the administration system has been modernised with a new
  design.

General improvements:

- The user interface now uses version 2.2.10 of the Django framework.

- The user interface is now consistently presented in Danish.

- The documentation has been updated for the 3.x series.

- Report module:

  - Files with several matches are presented more cleanly.

  - The user interface is correctly displayed with Internet Explorer 11.

- Scanner engine:

  - The old scanner engine has been entirely removed.

  - Formatted text is now processed more quickly and more reliably.

  - More image formats are supported for OCR.

  - Disk space usage has been reduced, and performance has been improved.

Bugfixes:

- Document metadata is now more relevant.

- Idle connections to network drives are now cleaned up more aggressively.

- It is now possible to log out of the report module cleanly.

- OCR is no longer performed on very small images.

- Copying file paths in the report module works properly again.

Version 3.0.0, 20th December 2019
---------------------------------

"Gift-Wrapped Under the Tree"

This is the first release of the 3.x release series of OS2datascanner.

New in this version:

- A new, extensible scanner engine:

  - Root privileges are no longer needed to mount remote network drives.

  - Elements in compound documents can now be uniquely identified.

    - Page numbers in PDF documents are tracked.

    - Full paths to files found in Zip files are now tracked.

  - Resources are only downloaded when needed and are immediately cleaned up.

    - Disk space requirements have been drastically reduced.

  - Support for scanning Office 365 mail installations.

  - Support for extracting metadata from scanned objects.

  - New sources of scannable objects can be added to the system.

- A new, extensible rule engine:

  - CPR rules and regular expression rules have been separated.

  - Logical operators (with short-circuiting) can be used to combine rules
    together.

  - New kinds of rules can be added to the system.

- A new scanner pipeline:

  - Scans are now performed by a pipeline of independent stateless processes
    which communicate by message passing.

    - All database interactions have been removed, drastically improving
      performance.

    - Scalability built-in: extra copies of any process can be started to
      improve performance.

  - Security:

    - Individual pipeline processes run in restricted sandboxes and
      do not have access to most system resources.

    - Scan results are filtered to avoid exposing sensitive information.

- A new report module:

  - The report module is now an independent component and not part of the
    administration system.

    - Users no longer need access to the administration system to read
      reports, reducing the attack surface of the administration system.

  - The interface has been modernised with a new design.

  - Flexibility: results from the pipeline are stored in the database in
    JSON format.

    - All results can be stored, even those not (yet) supported by the report
      module.

  - Targeted reports: users can now be shown only those results for which
    they have responsibility.

    - Support for associating metadata from scanned objects with users.

  - Historical results are stored.

  - Explanations are always available for why a file was, or was not,
    scanned.

  - Initial support for integrating external identity providers.

    - Support for assigning results to users based on Active Directory SID
      values.

- Reorganisation of the codebase for better modularity and code sharing.

- Integration with Prometheus for monitoring of performance and reliability.

- Structured logging for detailed information about internal system
  behaviour.
