alter table os2webscanner_scan add    "blacklisted_names" text NOT NULL default '';
alter table os2webscanner_scan add    "whitelisted_addresses" text NOT NULL default '';
alter table os2webscanner_scan add    "blacklisted_addresses" text NOT NULL default '';
