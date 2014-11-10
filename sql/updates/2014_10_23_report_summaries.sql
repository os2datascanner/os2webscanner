CREATE TABLE "os2webscanner_summary_scanners" (
    "id" serial NOT NULL PRIMARY KEY,
    "summary_id" integer NOT NULL,
    "scanner_id" integer NOT NULL REFERENCES "os2webscanner_scanner"
    ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("summary_id", "scanner_id")
)
;
CREATE TABLE "os2webscanner_summary" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(256) NOT NULL UNIQUE,
    "description" text,
    "schedule" text NOT NULL,
    "last_run" timestamp with time zone,
    "organization_id" integer NOT NULL
    REFERENCES "os2webscanner_organization"
    ("id") DEFERRABLE INITIALLY DEFERRED
)
;
ALTER TABLE "os2webscanner_summary_recipients" ADD CONSTRAINT "summary_id_refs_id_1f7a2657" FOREIGN KEY ("summary_id") REFERENCES "os2webscanner_summary" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "os2webscanner_summary_scanners" ADD CONSTRAINT "summary_id_refs_id_57965454" FOREIGN KEY ("summary_id") REFERENCES "os2webscanner_summary" ("id") DEFERRABLE INITIALLY DEFERRED;
