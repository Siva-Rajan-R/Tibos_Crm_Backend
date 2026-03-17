from elasticsearch import AsyncElasticsearch
from core.settings import SETTINGS

ES=AsyncElasticsearch(
    SETTINGS.ELASTIC_SEARCH_URL,
    basic_auth=("elastic","nz0mz-aEk9nPVRK2c-x_"),
    verify_certs=False
)