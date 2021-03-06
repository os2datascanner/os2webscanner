ALTER TABLE "os2webscanner_scanner" ADD COLUMN "do_last_modified_check" boolean NOT NULL DEFAULT TRUE;
ALTER TABLE "os2webscanner_scanner" ADD COLUMN "do_last_modified_check_head_request" boolean NOT NULL DEFAULT TRUE;

CREATE TABLE "os2webscanner_urllastmodified" (
    "id" serial NOT NULL PRIMARY KEY,
    "url" varchar(2048) NOT NULL,
    "last_modified" timestamp with time zone,
    "scanner_id" integer NOT NULL REFERENCES "os2webscanner_scanner" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "os2webscanner_urllastmodified_links" (
    "id" serial NOT NULL PRIMARY KEY,
    "from_urllastmodified_id" integer NOT NULL,
    "to_urllastmodified_id" integer NOT NULL,
    UNIQUE ("from_urllastmodified_id", "to_urllastmodified_id")
)
;
ALTER TABLE "os2webscanner_urllastmodified_links" ADD CONSTRAINT "from_urllastmodified_id_refs_id_fd37d138" FOREIGN KEY ("from_urllastmodified_id") REFERENCES "os2webscanner_urllastmodified" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "os2webscanner_urllastmodified_links" ADD CONSTRAINT "to_urllastmodified_id_refs_id_fd37d138" FOREIGN KEY ("to_urllastmodified_id") REFERENCES "os2webscanner_urllastmodified" ("id") DEFERRABLE INITIALLY DEFERRED;