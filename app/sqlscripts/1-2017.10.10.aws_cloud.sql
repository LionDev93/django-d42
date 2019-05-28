CREATE TABLE device42_cloudmodel (
    id SERIAL PRIMARY KEY,
    name character varying(64) NOT NULL,
    email character varying(254) NOT NULL,
    cloud_url character varying(256),
    cloud_password character varying(64) NOT NULL,
    time_linked timestamp with time zone NOT NULL,
    ip_address character varying(80),
    clicky_cookie character varying(128),
    intercom_id character varying(128),
    download_uuid character varying(36),
    active boolean,
    activation_uuid character varying(36)
);

alter table device42_cloudmodel owner to d42user;

alter sequence device42_cloudmodel_id_seq RESTART WITH 1142;
