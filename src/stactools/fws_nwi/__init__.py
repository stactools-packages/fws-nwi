import stactools.core
from stactools.cli.registry import Registry

stactools.core.use_fsspec()


def register_plugin(registry: Registry) -> None:
    from stactools.fws_nwi import commands

    registry.register_subcommand(commands.create_fwsnwi_command)


__version__ = "0.1.0"
