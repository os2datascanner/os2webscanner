CREATE TABLE "os2webscanner_urllastmodified" (
    "id" serial NOT NULL PRIMARY KEY,
    "url" varchar(2048) NOT NULL,
    "last_modified" timestamp with time zone
)
;