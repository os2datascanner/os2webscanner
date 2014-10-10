alter table os2webscanner_organization add "do_use_groups" boolean NOT NULL default false;
alter table os2webscanner_scanner add "group_id" integer REFERENCES "os2webscanner_group" ("id") DEFERRABLE INITIALLY DEFERRED;
alter table os2webscanner_domain add "group_id" integer REFERENCES "os2webscanner_group" ("id") DEFERRABLE INITIALLY DEFERRED;
alter table os2webscanner_regexrule add "group_id" integer REFERENCES "os2webscanner_group" ("id") DEFERRABLE INITIALLY DEFERRED;
alter table os2webscanner_userprofile add  "is_group_admin" boolean NOT NULL default false;

