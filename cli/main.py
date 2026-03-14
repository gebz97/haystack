import click
from tools.helpers import load_config
from cli.packages import packages
from cli.hosts import hosts

@click.group()
@click.pass_context
def main(ctx):
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config()
    
main.add_command(packages)
main.add_command(hosts)