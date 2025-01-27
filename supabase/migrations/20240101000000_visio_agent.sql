create table diagram_metadata (
    id uuid primary key,
    created_at timestamp with time zone default now(),
    version text,
    components integer,
    routing_algorithm text,
    style_rules jsonb
);

create index idx_diagram_components on diagram_metadata using gin (style_rules); 