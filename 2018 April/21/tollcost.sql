CREATE SCHEMA IF NOT EXISTS :v_schema;

DROP TABLE IF EXISTS :v_schema.ptginfo;

DROP TABLE IF EXISTS :v_schema.tollrule;
DROP TABLE IF EXISTS :v_schema.tolllink;
DROP TABLE IF EXISTS :v_schema.tolldesc;

CREATE TABLE IF NOT EXISTS :v_schema.ptginfo (
  prn_code    NUMERIC(2) NOT NULL,
  ntoll_type  NUMERIC(1) NOT NULL,
  bstoll_type NUMERIC(1) NOT NULL,
  tstoll_type NUMERIC(1) NOT NULL,
  ltoll_type  NUMERIC(1) NOT NULL,
  tg_type     NUMERIC(1) NOT NULL,
  info_src    NUMERIC(1) NOT NULL
);



DROP TABLE IF EXISTS :v_schema.roadinfo;

CREATE TABLE IF NOT EXISTS :v_schema.roadinfo (
  roadinfo_id NUMERIC(6) NOT NULL ,
  rname_chn CHARACTER VARYING(64) NOT NULL ,
  rname_eng CHARACTER VARYING(160) NOT NULL ,
  ralias_chn CHARACTER VARYING(64),
  route_no CHARACTER VARYING(48),
  ntoll_cate NUMERIC(4) NOT NULL ,
  ltoll_flag NUMERIC(1) NOT NULL ,
  ltoll_cate NUMERIC(4) NOT NULL ,
  discnt CHARACTER VARYING,
  note NUMERIC(1) NOT NULL
  --create_time TEXT,
  --update_time TEXT
);


DROP TABLE IF EXISTS :v_schema.ntollinfo;

CREATE TABLE IF NOT EXISTS :v_schema.ntollinfo (
  ntoll_cate  NUMERIC(4) NOT NULL,
  auto_type   CHAR(1)    NOT NULL,
  ntoll_base  FLOAT,
  ntoll_incrs FLOAT,
  info_src    NUMERIC(1) NOT NULL
);


DROP TABLE IF EXISTS :v_schema.bstoll;

CREATE TABLE IF NOT EXISTS :v_schema.bstoll (
  bstoll_id    NUMERIC(6)             NOT NULL,
  bname_chn    CHARACTER VARYING(64)  NOT NULL,
  bname_eng    CHARACTER VARYING(160) NOT NULL,
  auto_type    CHAR(1)                NOT NULL,
  bstoll_base  FLOAT,
  bstoll_incrs FLOAT,
  bst_flag     NUMERIC(1),
  ltoll_cate   NUMERIC(4)             NOT NULL,
  info_src     NUMERIC(1)             NOT NULL
  --create_time TEXT,
  --update_time TEXT
);

DROP TABLE IF EXISTS :v_schema.tstoll;

CREATE TABLE IF NOT EXISTS :v_schema.tstoll (
  tstoll_id    NUMERIC(6)             NOT NULL,
  tname_chn    CHARACTER VARYING(64)  NOT NULL,
  tname_eng    CHARACTER VARYING(160) NOT NULL,
  auto_type    CHAR(1)                NOT NULL,
  tstoll_base  FLOAT,
  tstoll_incrs FLOAT,
  tst_flag     NUMERIC(1),
  ltoll_cate   NUMERIC(4)             NOT NULL,
  info_src     NUMERIC(1)             NOT NULL
  --create_time TEXT,
  --update_time TEXT
);

DROP TABLE IF EXISTS :v_schema.nloadtoll;

CREATE TABLE IF NOT EXISTS :v_schema.nloadtoll (
  nltoll_cate NUMERIC(4) NOT NULL,
  nload_bnd   FLOAT      NOT NULL,
  nload_toll  FLOAT      NOT NULL,
  nload_unit  NUMERIC(1) NOT NULL,
  nload_type  NUMERIC(1) NOT NULL,
  info_src    NUMERIC(1) NOT NULL
);

DROP TABLE IF EXISTS :v_schema.oloadtoll;

CREATE TABLE IF NOT EXISTS :v_schema.oloadtoll (
  oltoll_cate NUMERIC(4) NOT NULL,
  oload_rate  FLOAT      NOT NULL,
  oload_toll  FLOAT      NOT NULL,
  oltoll_unit NUMERIC(1) NOT NULL,
  oltoll_type NUMERIC(1) NOT NULL,
  info_src    NUMERIC(1) NOT NULL
);

DROP TABLE IF EXISTS :v_schema.tginfo;

CREATE TABLE IF NOT EXISTS :v_schema.tginfo (
  tginfo_id   NUMERIC(7)             NOT NULL,
  tgname_chn  CHARACTER VARYING(64)  NOT NULL,
  tgname_eng  CHARACTER VARYING(160) NOT NULL,
  rname_chn   CHARACTER VARYING(64),
  rname_eng   CHARACTER VARYING(160),
  angle       NUMERIC(8, 4)          NOT NULL,
  auto_type   CHAR(1)                NOT NULL,
  tgtoll_base FLOAT,
  ltoll_flag  NUMERIC(1)             NOT NULL,
  ltoll_cate  NUMERIC(4)             NOT NULL,
  x_entr      NUMERIC(16, 6)         NOT NULL,
  y_entr      NUMERIC(16, 6)         NOT NULL,
  last_tg     CHARACTER VARYING(64),
  next_tg     CHARACTER VARYING(64),
  discnt      CHARACTER VARYING
);

DROP TABLE IF EXISTS :v_schema.autotype;

CREATE TABLE IF NOT EXISTS :v_schema.autotype (
  prn_code   NUMERIC(2) NOT NULL,
  auto_type  CHAR(1)    NOT NULL,
  auto_cate  NUMERIC(1) NOT NULL,
  min        NUMERIC    NOT NULL,
  max        NUMERIC    NOT NULL,
  unit       CHAR(1)    NOT NULL,
  auto_type2 NUMERIC(1) NOT NULL
);

DROP VIEW IF EXISTS :v_schema.config;
DROP TABLE IF EXISTS :v_schema.fee;

CREATE TABLE IF NOT EXISTS :v_schema.fee (
  id numeric NOT NULL,
  base NUMERIC(8,2) NOT NULL,
  incrs NUMERIC(8,2) NOT NULL,
  CONSTRAINT fee_pkey PRIMARY KEY (id)
);


-- DROP TABLE IF EXISTS :v_schema.config;

CREATE TABLE IF NOT EXISTS public.mapping (
  id numeric NOT NULL,
  prn_code numeric NOT NULL,
  type character(1) NOT NULL,
  sub_type numeric(1,0) NOT NULL,
  name character varying(64),
  route_no character varying(64),
  alias character varying(1000),
  CONSTRAINT mapping_pkey PRIMARY KEY (id)
);

DROP INDEX IF EXISTS mapping_n_unque_key;
CREATE UNIQUE INDEX mapping_n_unque_key ON public.mapping (prn_code, type, sub_type, name, route_no, alias) WHERE type = 'N';

DROP INDEX IF EXISTS mapping_bt_unque_key;
CREATE UNIQUE INDEX mapping_bt_unque_key ON public.mapping (prn_code, type, sub_type, name,alias) WHERE type IN ('B', 'T');

CREATE OR REPLACE VIEW :v_schema.config AS
SELECT m.*, f.base, f.incrs FROM public.mapping m INNER JOIN :v_schema.fee f on m.id = f.id order by m.id;
