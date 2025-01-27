@pytest.fixture(scope="session")
def supabase_mock():
    from supabase import Client
    return Client(
        supabase_url="http://localhost:8000",
        supabase_key="local-test-key"
    ) 