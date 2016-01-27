ALTER TABLE os2webscanner_organization ADD "cpr_whitelist" text NOT NULL DEFAULT '';
ALTER TABLE os2webscanner_scanner ADD  "whitelisted_cprs" text NOT NULL DEFAULT '';
