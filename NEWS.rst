* Version 2.2.1.2, May 10. 2019

Hotfix:
   - Add indices to UrlLastModified to speed up incremental web scans of very large sites.

* Version 2.2.1.1, May 10. 2019

Hotfix:
   - PDF processor was marking pdf conversions as an error if a syntax error occured. That is too harsh. Now a conversion is only marked as failure if the file was not a pdf or if pdf could not be converted.

* Version 2.2.1, May 7. 2019

New in this version:
    - Bugfix: Processors closed with SigTerm signal is now being teared down properly.
    - Enhancement: Extra logging added to libreoffice processor and process manager.

* Version 2.2.0, April 26. 2019

New in this version:
    - Bugfix: File scans sometimes contained broken links due to files being removed or deleted during scan.
    - Bugfix: Some file paths contained URL encoded characters which the scanner could not handle. It can now.
    - Enhancement: File scans now ignore hidden files, like the lock file `~okument1.docx`. Statistics are gathered on the number of these files.
    - Bugfix: Editing a scanner job would sometimes corrupt its values.
    - Enhancement: File domains can now contain spaces.
    - Enhancement: Reports are now divided into tabs.
    - Enhancement: Better error handling for LibreOffice processors.

* Version 2.1.0, March 15. 2019

New in this version:
    - CPR rule is no longer located on the scannerjob model.
    - Matches now have Windows friendly paths.
    - Clicking a path in a filescan report will automatically copy it to the clipboard.
    - Ordinary users can create domains again.
    - Better handling of Libreoffice processes.
    - Dead links found during webscan can be viewed properly in the report again.
    - Interface for validating domains works again.
    - A number of bug fixes: #27664, #27407 and #27037

* Version 2.0.0, January 17. 2019

New in this version:
    - Exchange scan is now supported. The exchange folders are downloaded first, and when finished, a file scan is started on the downloaded data.
    - Starting new scanjobs is now done using rabbitmq.
    - Scans are now only processing files the datascanner supports. That would be: text, csv, xml, html, pdf, image files (jpg, png, tiff, gif), ms office files.
    - XML processor added.
    - Better error handling during scans.
    - A number of bug fixes: #26044, #26727 (the most important one. Sitemap processing was not always done before scan started), #24001, #25362

* Version 1.8.0.6, September 25. 2018

Hotfix:
    - Cherrypicked enhancements made during filescan dev.
    - Now run.py store_stats method makes sure only one statistics object can be present. Before the fix the error corrupted the scanjob report and made it return http 500.
    - Some html pages resulted in a unicodedecodeerror during scan. They are now in a try except block.
    - Detecting encoding is now done by a method in utils.py using chardet.

* Version 1.8.0.5, August 20. 2018

Hotfix:
    - Fixed change password page so it does not return error code 500.
    - Fixed orgs and domains page so it does not return error code 500.
    - Removed unneccesary logging from scanner log showed in the final report.

* Version 1.8.0.4, August 14. 2018

Hotfix:
 - Fixed cron job error. Due to inheritance scanner.domains is on subclass level. Cron job now collects scanners with subclass type.

* Version 1.8.0.3, August 10. 2018

Hotfix:
 - Corrected indexerror during processor logging.

* Version 1.8.0.2, August 8. 2018

Hotfix:
 - cron.py was failing due to wrong import path.
 - Migration was failing. Corrected error.
 - In production the number of processors should be 8.

* Version 1.8.0.1, July 30. 2018

Hotfix:
 - Webscanner threw an error when extracting response objects that are files. Is now checking if response object is a HTMLResponse object.
 - Default email address is changed from info@magenta-aps.dk to os2webscanner@magenta-aps.dk which is the mail group related to webscanner.

* Version 1.8.0, June 20. 2018

New in this version:
 - Network share scan feature is added.
 - Ad hoc rules can now be combined into a set of rules.
 - Models.py file has been refactored from one very large file to many small.
 - Simple scan statistics have been added to reports.
 - Upgraded to django 1.11.9

* Version 1.7.1, May 28. 2018

Hotfix:
 - Now ignores if digital rights management bit is set for pdf files.
 - Enhanced logging for pdftohtml conversion subprocess call.
 - UnicodeEncodeError fixed when doing md5 calculation.

* Version 1.7.0, May 25, 2018

Hotfix:
 - Webscanner now uses latest version of Scrapy 1.5.0. This solves https scanning problems.

* Version 1.6.1, December 6, 2017

New in this:

 - Rules and Organization are now on the same page divided by tabs.
 - Reports and Summaries  are now on the same page divided by tabs.
 - Front page now contains tiles.
 - 'Scannere' is changed to 'Scannerjobs'.
 - English words in the interface are changed to danish.

* Version 1.6.0.1, May 8, 2017

Hotfix:

 - Limit broken links to 100 for consistency with critical matches (and
   performance).
 - Don't allow customer's user admin to set the "is_staff" flag (for
   now).


* Version 1.6.0, May 2, 2017

New in this version:

 - User administration for site superusers and reset password function
   for all users.
 - Reports page is paginated to reduce load time.
 - Visual cue if report has broken links or critical matches.
 - Better indication of how to find broken links on the scanned pages.
 - Bug fix: Scan no longer fails if broken link scan is on and an
   invalid URL is encountered.


* Version 1.5.2, March 16, 2017

New in this version:

 - Change subject of scan mail to include clear warning if critical
   matches.
 - It's now possible for organizations to only receive mail if scans
   have critical matches.


* Version 1.5.1.1, April 1, 2016

Hotfix:

 - Committed migration for the CPR whitelist fields.
 - Added new system dependency on mailutils.

* Version 1.5.1, April 1, 2016


New in this version:

 - Simple, cron-based monitoring of the process_manager program.


* Version 1.5.0, March 30, 2016

New in this version:

 - New, more inclusive CPR number rule.
 - Local whitelists for CPR numbers.
 - Upgraded to Django 1.8


* Version 1.4.1.3, March 23, 2016

Hotfix:

 - Handle multiline regular expressions, cutoff if the match exceeds
   1024 characters.


* Version 1.4.1.2, February 23, 2016

Hotfix:

 - Don't crash if sitemap URLs have errors, just log it and keep going.


* Version 1.4.1.1, October 23, 2015

New in this version:

 - Better handling of PDF files in latin-1.


* Version 1.4.1, October 13, 2015

New in this version:

 - Fix bug in LibreOffice conversion


* Version 1.4.0, June 12, 2015

New in this version:

 - Hide ad hoc scanners created for spreadsheet scans.
 - Introduce job to clean up non-terminating LibreOffice processes.
 - Consistent branding throughout (the product's name is 'OS2Webscanner'
   and nothing else).
 - Include context and page number for CPR matches to make them easier
   to find.
 - Check Last-Modified in meta http-equiv HTML headers.
 - Visibly mark links in reports as visited.
 - Performance: Save MD5 sums of binary files to avoid scanning the same
   file several times.
 - Better diagnostic information when conversion fails.
 - Collect cookies (so far only server-side cookies are supported).
 - Fix bugs in and improve installation guide.
 - Proper OCR of documents that are scanned upside down.
 - Improve layout of report.
 - More consistent terminology.
 - Include information about cookies in summary report.


* Version 1.3.3, March 13, 2015

New in this version:

 - Make it possible to limit scanning of spreadsheets to certain columns.


* Version 1.3.2, March 5, 2015

New in this version:

 - Delivery to Slagelse approved and stabilized.
 - Fixed encoding issue by adding a UTF-8 BOM to the CSV output file.


* Version 1.3.1.3, February 23, 2015

Hotfix:

 - Allow domains to be excluded, i.e. allow subdomain to be excluded from a
   *-domain.


* Version 1.3.1.2, February 18, 2015

Hotfix:

 - Add init script for automatic start of process manager.


* Version 1.3.1.1, February 18, 2015

Hotfix:

 - Fix UnicodeEncodeError when users uploaded a spreadsheet with Danish
   characters in file name.


* Version 1.3.1, February 5, 2015

New in this version:

 - Address scanning adjusted to give a match whenever a valid street name is
   found and a critical match if a street name is found with a house number.
 - Name scanning will eliminate leading and tailing capitalized words to
   avoid false negatives.


* Version 1.3.0.1, January 28, 2015

Hotfix:

 - Format of returned CSV fixed.


* Version 1.3.0, January 28, 2014

New in this version:

 - Support for spreadsheets with the option to modify (hide) data found by
   the address, name or CPR rule.
 - Name scanning enhanced to support more liberal formatting of names,
   including hyphen-concatenation and abbreviations.
 - Address scanning is implemented. In order to yield a match, at least an
   existing Danish streetname must be found. 
 - A special web client - basically, an upload form - allows users to upload
   spreadsheets for scanning. A new "upload only" user profile of users who can
   *only* access that upload form and nothing else.
 - For each organisation, a global whitelist and blacklist has been added for
   name and address scanning.
 - Whitelists and blacklists are available under the menu item "Oplæring".
 - Reports from scanning of spreadsheets are visible in the reports list - as
   opposed to the reports from API calls in previous versions.
 - CSV output files always use semicolon as separator (not comma, and not
   defaults).
 - Default values for replacement text is fixed as "NAVN" for name rule,
   "ADRESSE" for address rule and "xxxxxx-xxxx" for CPR rule.
 - Bug fix: Name scanning will now match names with more than two middle names.
 - Bug fix: Don't attempt to link to file URLs.
 - Bug fix: Domains are not listed on report when scanning files or scanning
   URL list through API.
 - Bug fix: Blacklisting of street names and not just individual addresses now
   works.

NOTE: All of the functionality in this release has been requested and funded by
Slagelse Kommune.


* Version 1.2.0, November 14, 2014

New in this version:
 - Summary report - summaries of certain scanners' results which may be
   emailed to users.
 - Automatic retrieval of sitemap.xml, i.e. no explicit upload required.
 - You can now specify a number of individual recipients of scan reports.
   The organization contact will no longer receive these emails by default.
 - Details of specific scan are always copied to the scan report; a technical
   occurrence log has been added to the report to help diagnose scan failures
   and conversion errors, etc.
 - Minimize false positives: Many more irrelevant CPR matches are ignored.
 - Group concept to enforce access limitations within one organization is
   mostly implemented; due to some issues, its use is discouraged until next
   sprint.
 - CSV file with report was broken in some cases.
 - Overview page listing domains per organisation is now available for
   superusers.
 - Pooling of PostgreSQL connections is now possible (but STRONGLY
   DISCOURAGED!)
 - Scanner listing is now sorted by date.
 - The Name rule has been completely removed from the GUI.
 - Small images are ignored, i.e. not OCR'ed.
 - Organization is included in all lists where relevant (superuser only).
 - Scheduled scans didn't run if set for specific dates.
 - Admin-related menu items have been consolidated in an admin menu.
 - Installation instructions have been updated and now work.
 - Installation instructions include how to set up crontab for scheduled
   scanning.
 - Links in scan reports now open in a new window.
 - Minimize false positives: CPR matches are ignored in inline style tags.
 - New widget to maintain many to many links, including a search field to
   support very long lists.
 - Improved GUI design.
 - Spreadsheets in formats XLSX/XLS/ODS are now scanned correctly.
 - Improvements and bug-fixes to the XML-RPC interface.
 - Sample RPC client has been improved significantly and now supports passing
   parameters for the scan, and saving the report to a CSV file.
 - Schedule information now shown as Yes/No in scanner list.
 - Documents sent and scanned via XML-RPC now retain file names in the URL.


* Version 1.1.0.5, November 4, 2014

 - Bug fix: Failed conversion items did not get their temporary directories
   removed.
 - Better error handling in processing of conversion items if an
   image's dimensions cannot be determined.


* Version 1.1.0.4, October 29, 2014

 - Performance improvement: When the number of OCR items per scan reaches a
   certain limit, non-OCR conversions are paused to allow the number of OCR
   items to fall to a reasonable level before being resumed again. For large
   scans with OCR enabled, this is necessary because so many OCR items are
   extracted from PDFs or Office documents that it exhausts the number of
   available inodes on the filesystem.
 - Connnection pooling is removed due to database problems.


* Version 1.1.0.3, October 10, 2014

New in this version:

 - Bug fix: Catch InternalError exception in process_manager.py.
 - Conversion queue items of a given type are now picked randomly from among
   the active scans to avoid one scan hogging the queue.


* Version 1.1.0.2, October 10, 2014

New in this version:

 - Bug fix: CPR check using wrong digit to validate birth date. The CPR rule
   was using the 8th digit instead of the 7th digit of the CPR number to
   validate the birth date of CPR numbers.
 - Periodically delete conversion queue items from finished scans that may
   not have been properly cleaned up when they finished.
 - Ignore and delete images extracted from converted files if their are
   dimensions do not meet minimum dimensions: both width and height must be
   >= 7 pixels and at least one dimension must be >= 64 pixels.
 - Scans are logged to separate files in var/logs/scans rather than
   polluting the web server's error log file.
 - Pool PostgreSQL connections to avoid too heavy load on the database server.
 - System status page for superusers.


* Version 1.1.0, September 23, 2014

New in this version:

 - Better parsing of names to avoid false positives.
 - Linkchecker functionality included.
 - Modulus-11 tweaking.
 - A huge number of minor GUI fixes.
 - Web service for scanning URLs or documents from other programs etc.
 - Set proper permissions for scan data. 
 - Use Last-Modified check to disregard previous scans.
 - Allow scanning of subdomains.
 - Disk usage/disk performance improvements.
 - 10 seconds timeout on PDF files in the link checker.
