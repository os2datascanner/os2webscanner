alter table  os2webscanner_scan add "is_visible" boolean NOT NULL default false;
update os2webscanner_scan scan set is_visible = (select is_visible from os2webscanner_scanner scanner  where scanner.id = scan.scanner_id);
