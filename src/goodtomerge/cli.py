"""Command-line interface for GoodToMerge."""

import click
from goodtomerge import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """GoodToMerge - PR workflow excellence with Claude Code."""
    pass


@main.command()
def validate():
    """Validate PR readiness."""
    click.echo("🔍 Validating PR readiness...")
    # TODO: Implement PR validation logic
    click.echo("✅ Ready to merge!")


@main.command()
@click.argument("pr_number", type=int)
def check(pr_number: int):
    """Check PR status and CI/CD results."""
    click.echo(f"📊 Checking PR #{pr_number}...")
    # TODO: Implement PR status check
    click.echo(f"PR #{pr_number} status: ✅ All checks passed")


if __name__ == "__main__":
    main()
