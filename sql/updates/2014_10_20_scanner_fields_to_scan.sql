
CREATE TABLE "os2webscanner_scan_regex_rules" (
    "id" serial NOT NULL PRIMARY KEY,
    "scan_id" integer NOT NULL,
    "regexrule_id" integer NOT NULL REFERENCES "os2webscanner_regexrule" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("scan_id", "regexrule_id")
)
;
CREATE TABLE "os2webscanner_scan_domains" (
    "id" serial NOT NULL PRIMARY KEY,
    "scan_id" integer NOT NULL,
    "domain_id" integer NOT NULL REFERENCES "os2webscanner_domain" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("scan_id", "domain_id")
)
;

ALTER TABLE "os2webscanner_scan" ADD "whitelisted_names" text NOT NULL DEFAULT '';
ALTER TABLE "os2webscanner_scan" ADD "do_cpr_scan" boolean NOT NULL DEFAULT TRUE;
ALTER TABLE "os2webscanner_scan" ADD "do_name_scan" boolean NOT NULL DEFAULT FALSE;
ALTER TABLE "os2webscanner_scan" ADD "do_ocr" boolean NOT NULL DEFAULT FALSE;
ALTER TABLE "os2webscanner_scan" ADD "do_cpr_modulus11" boolean NOT NULL DEFAULT TRUE;
ALTER TABLE "os2webscanner_scan" ADD "do_link_check" boolean NOT NULL DEFAULT FALSE;
ALTER TABLE "os2webscanner_scan" ADD "do_external_link_check" boolean NOT NULL DEFAULT FALSE;
ALTER TABLE "os2webscanner_scan" ADD "do_last_modified_check" boolean NOT NULL DEFAULT TRUE;
ALTER TABLE "os2webscanner_scan" ADD "do_last_modified_check_head_request" boolean NOT NULL DEFAULT TRUE;
