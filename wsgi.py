import click

from api import create_app

api = create_app()


@api.cli.command("list-routes")
@click.argument("blueprint_name", required=False)
def list_routes(blueprint_name=None):
    output = []
    for rule in api.url_map.iter_rules():
        if not blueprint_name or (rule.blueprint == blueprint_name):
            output.append(f"{rule.endpoint:<30} {rule.rule}")

    click.echo("\n".join(sorted(output)))


if __name__ == "__main__":
    api.run(host="0.0.0.0", port=5001, debug=False)
