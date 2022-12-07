import json
import os.path
from tempfile import TemporaryDirectory
from typing import Callable, List

from click import Command, Group
from pystac import Item
from stactools.testing.cli_test import CliTestCase

from stactools.fws_nwi.commands import create_fwsnwi_command

from . import test_data


class CommandsTest(CliTestCase):
    def create_subcommand_functions(self) -> List[Callable[[Group], Command]]:
        return [create_fwsnwi_command]

    def test_create_collection(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            dest_file = os.path.join(tmp_dir, "collection.json")

            result = self.run_command(f"fws-nwi create-collection {dest_file}")

            self.assertEqual(result.exit_code, 0, msg="\n{}".format(result.output))

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            collection = {}
            with open(dest_file) as f:
                collection = json.load(f)

            self.assertEqual(collection["id"], "fws-nwi")

    def test_create_item(self) -> None:
        path = test_data.get_path("data-files/DC_shapefile_wetlands.zip")
        with TemporaryDirectory() as temporary_directory:
            cmd = f"fws-nwi create-item {path} {temporary_directory}/item.json"
            result = self.run_command(cmd)
            self.assertEqual(result.exit_code, 0, msg="\n{}".format(result.output))

            files = os.listdir(temporary_directory)
            jsons = [p for p in files if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            item = Item.from_file(f"{temporary_directory}/{jsons[0]}")
            item.validate()

    def test_create_item_with_geoparquet(self) -> None:
        path = test_data.get_path("data-files/DC_shapefile_wetlands.zip")
        with TemporaryDirectory() as temporary_directory:
            cmd = f"fws-nwi create-item {path} {temporary_directory}/item.json --create-geoparquet"
            result = self.run_command(cmd)
            self.assertEqual(result.exit_code, 0, msg="\n{}".format(result.output))

            files = os.listdir(temporary_directory)
            geoparquets = [p for p in files if p.endswith(".geoparquet")]
            self.assertEqual(len(geoparquets), 4)
