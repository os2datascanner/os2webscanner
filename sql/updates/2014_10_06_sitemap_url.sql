ALTER TABLE "os2webscanner_domain" ADD COLUMN "sitemap_url" varchar(2048)
NOT NULL DEFAULT '';
ALTER TABLE "os2webscanner_domain" ADD COLUMN "download_sitemap" boolean NOT
NULL DEFAULT TRUE;