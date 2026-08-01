import os
import tempfile
import unittest
from unittest import mock
from zipfile import ZipFile

import createAllDB


class GtfsSourceTests(unittest.TestCase):
    def test_missing_url_file_has_no_urls(self):
        with tempfile.TemporaryDirectory() as city_dir:
            self.assertEqual(createAllDB.read_feed_urls(os.path.join(city_dir, "url.txt")), [])

    def test_url_is_preferred_when_available(self):
        with mock.patch.object(createAllDB, "download_and_unzip") as download, mock.patch.object(
            createAllDB, "extract_local_zips"
        ) as extract:
            source = createAllDB.load_gtfs_source(
                "City_Country",
                ["https://example.com/gtfs.zip"],
                ["City_Country/local.zip"],
                lambda message: None,
            )

        self.assertEqual(source, "url")
        download.assert_called_once()
        extract.assert_not_called()

    def test_local_zip_is_used_when_url_fails(self):
        warnings = []
        with mock.patch.object(
            createAllDB, "download_and_unzip", side_effect=RuntimeError("offline")
        ), mock.patch.object(createAllDB, "extract_local_zips") as extract:
            source = createAllDB.load_gtfs_source(
                "City_Country",
                ["https://example.com/gtfs.zip"],
                ["City_Country/local.zip"],
                warnings.append,
            )

        self.assertEqual(source, "local_zip")
        extract.assert_called_once()
        self.assertIn("falling back", warnings[0])

    def test_local_zip_is_imported_without_url_file(self):
        with tempfile.TemporaryDirectory() as city_dir:
            zip_path = os.path.join(city_dir, "monopoli.zip")
            with ZipFile(zip_path, "w") as archive:
                archive.writestr("gtfs/routes.txt", "route_id,route_short_name\n1,M1\n")

            local_zips = createAllDB.find_local_feed_zips(city_dir)
            source = createAllDB.load_gtfs_source(city_dir, [], local_zips, lambda message: None)

            self.assertEqual(source, "local_zip")
            with open(os.path.join(city_dir, "routes.txt"), encoding="utf8") as routes:
                contents = routes.read()
            self.assertIn("source_feed", contents)
            self.assertIn("M1", contents)


if __name__ == "__main__":
    unittest.main()
