from stactools.testing.test_data import TestData

EXTERNAL_DATA = {
    "HI_shapefile_wetlands.zip": {
        "url": (
            "https://www.fws.gov/wetlands/Data/State-Downloads/HI_shapefile_wetlands.zip"
        ),
    }
}

test_data = TestData(__file__, EXTERNAL_DATA)
