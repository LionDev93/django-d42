ALTER TABLE device42_downloadmodel ADD COLUMN request_cookies jsonb NULL;
ALTER TABLE device42_contactmodel ADD COLUMN request_cookies jsonb NULL;
ALTER TABLE device42_schedulemodel ADD COLUMN request_cookies jsonb NULL;
ALTER TABLE device42_updatemodel ADD COLUMN request_cookies jsonb NULL;
ALTER TABLE device42_cloudmodel ADD COLUMN request_cookies jsonb NULL;
alter table device42_idsprocessed add column id_processed_cloud integer;
update device42_idsprocessed set id_processed_cloud = 0;
