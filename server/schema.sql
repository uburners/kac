CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

SET ROLE kac;

CREATE TABLE IF NOT EXISTS event (
    id varchar(200) PRIMARY KEY,
    name text   
);


CREATE TABLE IF NOT EXISTS ticket (
    event_id varchar(200) REFERENCES event(id),
    code text,
    activated_at timestamp,
    PRIMARY KEY (event_id, code),
    UNIQUE(event_id, code)
);

CREATE TYPE token_status AS ENUM ('in', 'out');

CREATE TABLE IF NOT EXISTS access_token (
    event_id varchar(200) ,
    ticket_code text,
    token text,
    status token_status DEFAULT 'out',
    created_at timestamp DEFAULT now(),
    last_updated_at timestamp,

    ---
    txn_start timestamp,
    txn_gate_id varchar(200),

    PRIMARY KEY (event_id, token),
    FOREIGN KEY(event_id, ticket_code) REFERENCES ticket(event_id, code)
);


CREATE TYPE access_event_type AS ENUM ('enter', 'exit');

CREATE TABLE IF NOT EXISTS access_events (
    id uuid DEFAULT uuid_generate_v1() PRIMARY KEY,
    event_id varchar(200),
    token text,
    ts timestamp DEFAULT now(),
    action access_event_type,

    FOREIGN KEY (event_id, token) REFERENCES access_token(event_id, token)
);


CREATE TYPE turngate_direction AS ENUM ('enter', 'exit');


CREATE TABLE IF NOT EXISTS turngate (
    event_id varchar(200) REFERENCES event(id),
    turngate_id varchar(200),
    direction turngate_direction,

    PRIMARY KEY (event_id, turngate_id)
);



INSERT INTO public.event(id, name) VALUES ('2019_precomp', 'Precompression 2019 Housewarming');
INSERT INTO public.ticket(event_id, code) VALUES ('2019_precomp', '1234');
INSERT INTO public.turngate(event_id, turngate_id, direction) VALUES ('2019_precomp', '363eafe8d14c4700ac218f9f0f044e42', 'enter');
INSERT INTO public.turngate(event_id, turngate_id, direction) VALUES ('2019_precomp', '7baf48646d0c11e9ac6ee4b31884570b', 'exit');
