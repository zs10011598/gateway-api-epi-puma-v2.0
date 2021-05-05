DROP TABLE IF EXISTS mesh_state;
CREATE TABLE mesh_state (id serial, gridid_state varchar(2), name varchar(50), pobtot integer default 0);
ALTER TABLE mesh_state ADD CONSTRAINT pk_mesh_state UNIQUE(id);

DROP TABLE IF EXISTS mesh_mun;
CREATE TABLE mesh_mun (id serial, state_id integer, gridid_state varchar(2), 
	gridid_mun varchar(5), state_name varchar(50), name varchar(200), pobtot integer default 0);
ALTER TABLE mesh_mun ADD CONSTRAINT pk_mesh_mun UNIQUE(id);
ALTER TABLE mesh_mun ADD CONSTRAINT fk_mesh_mun_gridid_state FOREIGN KEY (state_id) REFERENCES mesh_state(id);


DROP TABLE IF EXISTS mesh_ageb;
CREATE TABLE mesh_ageb (id serial, state_id integer, gridid_state varchar(2), 
	mun_id integer, gridid_mun varchar(5), gridid_ageb varchar(10), state_name varchar(50), municipality_name varchar(200), 
	pobtot integer default 0);
ALTER TABLE mesh_ageb ADD CONSTRAINT pk_mesh_ageb UNIQUE(id);
ALTER TABLE mesh_ageb ADD CONSTRAINT fk_mesh_ageb_gridid_state FOREIGN KEY (state_id) REFERENCES mesh_state(id);
ALTER TABLE mesh_ageb ADD CONSTRAINT fk_mesh_ageb_gridid_mun FOREIGN KEY (mun_id) REFERENCES mesh_mun(id);

DROP TABLE IF EXISTS target_group_catalogue;
CREATE TABLE target_group_catalogue(id serial, name varchar(50));
ALTER TABLE target_group_catalogue ADD CONSTRAINT pk_target_group_catalogue UNIQUE(id);

INSERT INTO target_group_catalogue(name) VALUES('> 60'), ('50-59'), ('40-49'), ('HOMBRES'), ('MUJERES');

DROP TABLE IF EXISTS target_group_population_state;
CREATE TABLE target_group_population_state(id serial, target_group_id integer, state_id integer, population integer default 0);
ALTER TABLE target_group_population_state ADD CONSTRAINT pk_target_group_population_state UNIQUE(id);
ALTER TABLE target_group_population_state ADD CONSTRAINT fk_target_group_population_state_gridid_state FOREIGN KEY (state_id) REFERENCES mesh_state(id);

DROP TABLE IF EXISTS target_group_population_mun;
CREATE TABLE target_group_population_mun(id serial, target_group_id integer, state_id integer, 
	mun_id integer, population integer default 0);
ALTER TABLE target_group_population_mun ADD CONSTRAINT pk_target_group_population_mun UNIQUE(id);
ALTER TABLE target_group_population_mun ADD CONSTRAINT fk_target_group_population_mun_gridid_state FOREIGN KEY (state_id) REFERENCES mesh_state(id);
ALTER TABLE target_group_population_mun ADD CONSTRAINT fk_target_group_population_mun_gridid_mun FOREIGN KEY (mun_id) REFERENCES mesh_mun(id);

DROP TABLE IF EXISTS target_group_population_ageb;
CREATE TABLE target_group_population_ageb(id serial, target_group_id integer, state_id integer, 
	mun_id integer, ageb_id integer, population integer default 0);
ALTER TABLE target_group_population_ageb ADD CONSTRAINT pk_target_group_population_ageb UNIQUE(id);
ALTER TABLE target_group_population_ageb ADD CONSTRAINT fk_target_group_population_ageb_gridid_state FOREIGN KEY (state_id) REFERENCES mesh_state(id);
ALTER TABLE target_group_population_ageb ADD CONSTRAINT fk_target_group_population_ageb_gridid_mun FOREIGN KEY (mun_id) REFERENCES mesh_mun(id);
ALTER TABLE target_group_population_ageb ADD CONSTRAINT fk_target_group_population_ageb_gridid_ageb FOREIGN KEY (ageb_id) REFERENCES mesh_ageb(id);

CREATE INDEX idx_target_group_population_state_target_group_id on target_group_population_state(target_group_id);
CREATE INDEX idx_target_group_population_state_state_id on target_group_population_state(state_id);

CREATE INDEX idx_target_group_population_mun_target_group_id on target_group_population_mun(target_group_id);
CREATE INDEX idx_target_group_population_mun_state_id on target_group_population_mun(state_id);
CREATE INDEX idx_target_group_population_mun_mun_id on target_group_population_mun(mun_id);

CREATE INDEX idx_target_group_population_ageb_target_group_id on target_group_population_ageb(target_group_id);
CREATE INDEX idx_target_group_population_ageb_state_id on target_group_population_ageb(state_id);
CREATE INDEX idx_target_group_population_ageb_mun_id on target_group_population_ageb(mun_id);
CREATE INDEX idx_target_group_population_ageb_ageb_id on target_group_population_ageb(ageb_id);
