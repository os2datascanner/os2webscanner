ALTER table os2webscanner_scanner ADD column "do_link_check" boolean NOT NULL DEFAULT FALSE;
ALTER table os2webscanner_scanner ADD column "do_external_link_check" boolean NOT NULL DEFAULT FALSE;

ALTER table os2webscanner_url ADD column "status_code" integer;
ALTER table os2webscanner_url ADD column "status_message" varchar(256);

CREATE TABLE "os2webscanner_url_referrers" (
  "id" serial NOT NULL PRIMARY KEY,
  "url_id" integer NOT NULL,
  "referrerurl_id" integer NOT NULL,
  UNIQUE ("url_id", "referrerurl_id")
);

CREATE TABLE "os2webscanner_referrerurl" (
  "id" serial NOT NULL PRIMARY KEY,
  "url" varchar(2048) NOT NULL,
  "scan_id" integer NOT NULL REFERENCES "os2webscanner_scan" ("id") DEFERRABLE INITIALLY DEFERRED
);

ALTER TABLE "os2webscanner_url_referrers" ADD CONSTRAINT "referrerurl_id_refs_id_26b644ea" FOREIGN KEY ("referrerurl_id") REFERENCES "os2webscanner_referrerurl" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "os2webscanner_url_referrers" ADD CONSTRAINT "url_id_refs_id_76a3acdc" FOREIGN KEY ("url_id") REFERENCES "os2webscanner_url" ("id") DEFERRABLE INITIALLY DEFERRED;
