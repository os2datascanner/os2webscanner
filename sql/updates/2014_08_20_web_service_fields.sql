alter table os2webscanner_scanner add  "encoded_process_urls" varchar(262144);
alter table os2webscanner_scanner add  "do_run_synchronously" boolean NOT NULL default false;
alter table os2webscanner_scanner add  "is_visible" boolean NOT NULL default true;
