CREATE TABLE "os2webscanner_urllastmodified" (
    "id" serial NOT NULL PRIMARY KEY,
    "url" varchar(2048) NOT NULL,
    "last_modified" timestamp with time zone
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