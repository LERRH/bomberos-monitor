create table if not exists reports (
    nro_parte bigint primary key,
    fecha_hora timestamp,
    direccion text not null,
    lat double precision,
    lon double precision,
    tipo text not null,
    estado text not null,
    unidades text[] not null default '{}',
    first_seen_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now(),
    last_changed_at timestamptz not null default now()
);

create table if not exists report_history (
    id bigserial primary key,
    nro_parte bigint not null references reports(nro_parte),
    observed_at timestamptz not null default now(),
    estado text not null,
    unidades text[] not null default '{}',
    direccion text,
    lat double precision,
    lon double precision,
    tipo text
);

create index if not exists report_history_nro_parte_idx on report_history (nro_parte);
create index if not exists reports_fecha_hora_idx on reports (fecha_hora);

create table if not exists unit_reference (
    id bigserial primary key,
    comandancia_code text not null,
    comandancia_name text not null,
    cia_code text not null,
    unit_code text not null
);

create index if not exists unit_reference_unit_code_idx on unit_reference (unit_code);
