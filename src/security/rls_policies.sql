create policy "Diagram Metadata Access"
on diagram_metadata
using (
    auth.uid() = owner_id
    or exists (
        select 1 from team_members
        where team_id = diagram_metadata.team_id
        and user_id = auth.uid()
    )
); 