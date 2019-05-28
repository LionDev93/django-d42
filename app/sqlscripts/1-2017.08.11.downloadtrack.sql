CREATE TABLE "device42_downloadlinktrack" ("id" serial NOT NULL PRIMARY KEY);
ALTER TABLE "device42_downloadlinktrack" ADD COLUMN "downloadmodel_id" integer REFERENCES "device42_downloadmodel" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "device42_downloadlinktrack" ALTER COLUMN "downloadmodel_id" set NOT NULL;
alter table device42_idsprocessed add column id_processed_downloadlinktrack integer;
update device42_idsprocessed set id_processed_downloadlinktrack = 0;
