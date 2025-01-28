import yaml
import pytest

def load_docker_compose():
    with open('docker-compose.yml') as f:
        return yaml.safe_load(f)

def test_postgres_healthcheck():
    compose = load_docker_compose()
    pg = compose['services']['postgres']
    assert pg['healthcheck']['test'] == ["CMD-SHELL", "pg_isready -U visio"]
    assert pg['healthcheck']['interval'] == '5s'

def test_redis_healthcheck():
    compose = load_docker_compose()
    redis = compose['services']['redis']
    assert redis['healthcheck']['test'] == ["CMD", "redis-cli", "ping"]
    assert redis['healthcheck']['timeout'] == '3s' 