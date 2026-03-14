import click


@click.group()
@click.pass_context
def hosts(ctx):
    pass


@hosts.command()
def list():
    print("Listing hosts:...")