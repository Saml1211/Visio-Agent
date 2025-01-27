-- Diagram access control
create policy "Diagrams: Read access for owners/collaborators"
on diagrams for select using (
    auth.uid() = owner_id
    or exists (
        select 1 from diagram_collaborators
        where diagram_id = diagrams.id
        and user_id = auth.uid()
    )
);

-- Version history access
create policy "Versions: View version history"
on versions for select using (
    exists (
        select 1 from diagrams
        where diagrams.id = versions.diagram_id
        and (diagrams.owner_id = auth.uid()
             or exists (
                 select 1 from diagram_collaborators
                 where diagram_id = diagrams.id
                 and user_id = auth.uid()
             ))
    )
);

-- Routing metrics (admin only)
create policy "Routing metrics: Admin access"
on routing_metrics for all using (auth.role() = 'admin');

-- Add JWT configuration
create extension if not exists pgjwt;

create or replace function visio_auth() returns void as $$
begin
  execute format('alter role authenticator set pgrst.jwt_claim_headers = ''{"supabase": "https://%s", "iss": "visio-agent"}''', current_setting('visio.supabase_url'));
end;
$$ language plpgsql;

select visio_auth(); 