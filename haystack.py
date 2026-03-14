#!/v/bin/python

import click
from tools.helpers import get_db_con, get_vault_client, load_config, read_vault_data


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config()


@cli.command()
@click.pass_context
def package_report(ctx):
    pass


@cli.command()
@click.pass_context
def status(ctx):
    """Check Vault connectivity and auth."""
    conf = ctx.obj["config"]
    client = get_vault_client(conf)
    health = client.sys.read_health_status(method="GET")
    click.echo(f"Vault status: {'sealed' if health['sealed'] else 'unsealed'}")
    click.echo(f"Authenticated: {client.is_authenticated()}")


if __name__ == "__main__":
    cli()
