import json
import os.path
from tempfile import TemporaryDirectory
from typing import Callable, List

from click import Command, Group
from deepdiff import DeepDiff
from stactools.testing.cli_test import CliTestCase

from stactools.fws_nwi.commands import create_fwsnwi_command

from . import context


class CommandsTest(CliTestCase):
    def create_subcommand_functions(self) -> List[Callable[[Group], Command]]:
        return [create_fwsnwi_command]

    def test_create_collection(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            truth_file = os.path.join(context.SOURCE_FOLDER, "collection.json")
            dest_file = os.path.join(tmp_dir, "collection.json")

            result = self.run_command(
                f"fws-nwi create-collection {dest_file}"
                f" --start_time 2022-01-01T00:00:00Z"
            )

            self.assertEqual(result.exit_code, 0, msg="\n{}".format(result.output))

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            collection = {}
            truth_collection = {}
            with open(dest_file) as f:
                collection = json.load(f)
            with open(truth_file) as f:
                truth_collection = json.load(f)

            self.assertEqual(collection["id"], "fws-nwi")

            diff = DeepDiff(
                collection,
                truth_collection,
                ignore_order=True,
                exclude_regex_paths=r"root\['links'\]\[\d+\]\['href'\]",
            )
            if len(diff) > 0:
                print(diff)
            self.assertEqual(diff, {})

    def test_create_item(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            id = "DC_shapefile_wetlands"
            src_collection = os.path.join(context.SOURCE_FOLDER, "collection.json")
            truth_file = os.path.join(context.SOURCE_FOLDER, f"{id}.json")
            dest_file = os.path.join(tmp_dir, "item.json")
            date = "2020-01-01T00:00:00Z"

            cmd = (
                f"fws-nwi create-item {context.DC_FILE} {dest_file}"
                f" --collection {src_collection}"
                f" --datetime {date}"
            )

            result = self.run_command(cmd)
            self.assertEqual(result.exit_code, 0, msg="\n{}".format(result.output))

            files = os.listdir(tmp_dir)
            jsons = [p for p in files if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            item = {}
            truth_item = {}
            with open(dest_file) as f:
                item = json.load(f)
            with open(truth_file) as f:
                truth_item = json.load(f)

            self.assertEqual(item["id"], id)

            diff = DeepDiff(
                item,
                truth_item,
                ignore_order=True,
                exclude_regex_paths=r"root\['(assets|links)'\]\[[\w']+\]\['href'\]",
            )
            if len(diff) > 0:
                print(diff)
            self.assertEqual(diff, {})
