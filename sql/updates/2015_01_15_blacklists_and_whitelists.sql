alter table os2webscanner_organization add 
    "name_whitelist" text NOT NULL default '',
    "name_blacklist" text NOT NULL default '',
    "address_whitelist" text NOT NULL default '',
    "address_blacklist" text NOT NULL default '';
