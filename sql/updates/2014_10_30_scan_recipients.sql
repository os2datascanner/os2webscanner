
CREATE TABLE "os2webscanner_scanner_recipients" (
    "id" serial NOT NULL PRIMARY KEY,
    "scanner_id" integer NOT NULL,
    "userprofile_id" integer NOT NULL REFERENCES "os2webscanner_userprofile" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("scanner_id", "userprofile_id")
)
;

ALTER TABLE "os2webscanner_scanner_recipients" ADD CONSTRAINT "scanner_id_refs_id_6305d81f" FOREIGN KEY ("scanner_id") REFERENCES "os2webscanner_scanner" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE "os2webscanner_scan_recipients" (
    "id" serial NOT NULL PRIMARY KEY,
    "scan_id" integer NOT NULL,
    "userprofile_id" integer NOT NULL REFERENCES "os2webscanner_userprofile" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("scan_id", "userprofile_id")
)
;

ALTER TABLE "os2webscanner_scan_recipients" ADD CONSTRAINT "scan_id_refs_id_9275ac06" FOREIGN KEY ("scan_id") REFERENCES "os2webscanner_scan" ("id") DEFERRABLE INITIALLY DEFERRED;

