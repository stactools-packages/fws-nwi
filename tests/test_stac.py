from stactools.fws_nwi import stac


def test_create_collection() -> None:
    # Write tests for each for the creation of a STAC Collection
    # Create the STAC Collection...
    collection = stac.create_collection()
    collection.set_self_href("")

    # Check that it has some required attributes
    assert collection.id == "fws-nwi"
    # self.assertEqual(collection.other_attr...

    # Validate
    collection.validate()
