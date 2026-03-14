import hvac
import yaml
import urllib3
import sqlalchemy as sqa


def load_config() -> dict:
    with open("config/haystack.yaml") as f:
        return yaml.safe_load(f)


def get_vault_client(conf: dict) -> hvac.Client:
    skip_verify = bool(conf.get("vault_skip_verify", True))

    if skip_verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    client = hvac.Client(
        url=conf["vault_url"],
        token=conf["vault_token"],
        verify=not skip_verify,
    )
    if not client.is_authenticated():
        raise RuntimeError("Vault authentication failed — check your token")
    return client


def read_vault_data(client: hvac.Client, path: str) -> dict:
    resp = client.secrets.kv.v2.read_secret_version(
        mount_point="haystack",
        path=path,
        raise_on_deleted_version=True,
    )
    return resp["data"]["data"]


def get_db_con(client: hvac.Client) -> sqa.Engine:
    creds = read_vault_data(client, "creds/db")

    host = creds["host"]
    port = creds["port"] or 5432
    user = creds["user"]
    password = creds["password"]
    db = creds["db"]

    url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"

    return sqa.create_engine(url)