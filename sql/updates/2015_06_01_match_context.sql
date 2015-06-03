alter table os2webscanner_match add "match_context" varchar(1152) NOT NULL default '';
alter table os2webscanner_conversionqueueitem add "page_no" integer;
alter table os2webscanner_match add "page_no" integer;
