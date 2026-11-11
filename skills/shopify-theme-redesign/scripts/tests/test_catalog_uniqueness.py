import copy
import csv
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_catalog_uniqueness import Audit, public_url, product_url, Image


@unittest.skipIf(Image is None, "Pillow required for image-content tests")
class CatalogAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def site(self, sid, source_id, seed=1):
        rng = random.Random(seed)
        path = self.root / (sid + ".png")
        image = Image.new("RGB", (32, 32))
        image.putdata([(rng.randrange(256), rng.randrange(256), rng.randrange(256)) for _ in range(1024)])
        image.save(path)
        handle = "handle-" + str(source_id)
        source = "https://cdn.shopify.com/s/files/1/0000/files/" + str(source_id) + ".png?v=1"
        product = dict(handle=handle, product_key="supplier:" + str(source_id), family_key="style:" + str(source_id), source_product_id=str(source_id), source_url="https://supplier.test/products/" + str(source_id), identity_review="Source style code and photographed details checked.", images=[dict(source_url=source, path=path.name)])
        self.write_csv(sid + ".csv", [(handle, source, "")])
        return dict(site_id=sid, expected_products=1, products=[product], csv_paths=[sid + ".csv"], images=[])

    def write_csv(self, name, rows):
        with (self.root / name).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["URL handle", "Product image URL", "Variant image URL"])
            writer.writerows(rows)

    def run_audit(self, sites, history=None):
        path = self.root / "plan.json"
        path.write_text(json.dumps(dict(sites=sites)), encoding="utf-8")
        audit = Audit()
        audit.read(path)
        if history:
            other = self.root / "history.json"
            other.write_text(json.dumps(dict(sites=history)), encoding="utf-8")
            audit.read(other, "history")
        return audit.finish()

    def codes(self, result):
        return {entry["code"] for entry in result["findings"]}

    def test_distinct_final_catalogs_pass(self):
        result = self.run_audit([self.site("a", 1, 1), self.site("b", 2, 17)])
        self.assertEqual(result["exit_code"], 0, result)

    def test_renamed_handle_does_not_hide_same_source(self):
        a, b = self.site("a", 1), self.site("b", 1, 17)
        b["products"][0].update(product_key="invented:new", family_key="invented:family")
        self.assertIn("cross_site_product_family", self.codes(self.run_audit([a, b])))

    def test_aliases_merge_transitively(self):
        a, b, c = self.site("a", 1), self.site("b", 2, 17), self.site("c", 3, 31)
        a["products"][0]["alias_keys"] = ["supplier:2"]
        b["products"][0]["alias_keys"] = ["supplier:3"]
        result = self.run_audit([a, b, c])
        groups = [r for r in result["findings"] if r["code"] == "cross_site_product_family"]
        self.assertEqual(groups[0]["site_ids"], ["a", "b", "c"])

    def test_family_catches_colors_with_new_ids(self):
        a, b = self.site("a", 1), self.site("b", 2, 17)
        b["products"][0]["family_key"] = a["products"][0]["family_key"]
        self.assertIn("cross_site_product_family", self.codes(self.run_audit([a, b])))

    def test_cdn_size_change_does_not_hide_same_photo(self):
        a, b = self.site("a", 1), self.site("b", 2, 17)
        image = b["products"][0]["images"][0]
        image["source_url"] = "https://cdn.shopify.com/s/files/1/0000/files/1_600x.png?v=1&width=600"
        self.write_csv("b.csv", [("handle-2", image["source_url"], "")])
        self.assertIn("cross_site_photo", self.codes(self.run_audit([a, b])))

    def test_same_bytes_different_urls_caught(self):
        result = self.run_audit([self.site("a", 1), self.site("b", 2)])
        self.assertIn("cross_site_photo", self.codes(result))

    def test_lossless_reencoding_pixels_caught(self):
        a, b = self.site("a", 1), self.site("b", 2, 17)
        bmp = self.root / "b.bmp"
        Image.open(self.root / "a.png").save(bmp)
        b["products"][0]["images"][0]["path"] = bmp.name
        result = self.run_audit([a, b])
        self.assertIn("cross_site_photo", self.codes(result))

    def test_same_site_card_and_hero_reuse_allowed(self):
        a = self.site("a", 1)
        a["images"].append(copy.deepcopy(a["products"][0]["images"][0]))
        self.assertEqual(self.run_audit([a])["exit_code"], 0)

    def test_one_family_cannot_count_as_two_products_in_one_site(self):
        a = self.site("a", 1)
        second = copy.deepcopy(a["products"][0])
        second["handle"] = "renamed-handle"
        a["products"].append(second)
        a["expected_products"] = 2
        source = second["images"][0]["source_url"]
        self.write_csv("a.csv", [("handle-1", source, ""), ("renamed-handle", source, "")])
        self.assertIn("same_site_duplicate_product_family", self.codes(self.run_audit([a])))

    def test_registered_images_cannot_be_swapped_between_products(self):
        a, b = self.site("a", 1), self.site("b", 2, 17)
        a["products"].append(b["products"][0])
        a["expected_products"] = 2
        source_a = a["products"][0]["images"][0]["source_url"]
        source_b = a["products"][1]["images"][0]["source_url"]
        self.write_csv("a.csv", [("handle-1", source_b, ""), ("handle-2", source_a, "")])
        self.assertIn("unregistered_csv_image", self.codes(self.run_audit([a])))

    def test_same_primary_with_different_family_labels_still_needs_review(self):
        a, b = self.site("a", 1), self.site("b", 2)
        a["products"].append(b["products"][0])
        a["expected_products"] = 2
        self.write_csv("a.csv", [(p["handle"], p["images"][0]["source_url"], "") for p in a["products"]])
        result = self.run_audit([a])
        self.assertEqual(result["exit_code"], 2)
        self.assertIn("same_site_primary_photo_shared", self.codes(result))

    def test_product_and_other_site_hero_reuse_caught(self):
        a, b = self.site("a", 1), self.site("b", 2, 17)
        b["images"].append(copy.deepcopy(a["products"][0]["images"][0]))
        self.assertIn("cross_site_photo", self.codes(self.run_audit([a, b])))

    def test_url_only_not_claimed_content_checked(self):
        a = self.site("a", 1)
        del a["products"][0]["images"][0]["path"]
        result = self.run_audit([a])
        self.assertEqual(result["exit_code"], 2)
        self.assertIn("image_content_not_checked", self.codes(result))

    def test_missing_review_not_a_pass(self):
        a = self.site("a", 1)
        del a["products"][0]["identity_review"]
        self.assertIn("identity_not_reviewed", self.codes(self.run_audit([a])))

    def test_actual_csv_missing_product_caught(self):
        a = self.site("a", 1)
        self.write_csv("a.csv", [])
        self.assertIn("csv_manifest_mismatch", self.codes(self.run_audit([a])))

    def test_variant_image_must_be_registered(self):
        a = self.site("a", 1)
        self.write_csv("a.csv", [("handle-1", a["products"][0]["images"][0]["source_url"], "https://test.example/not-registered.jpg")])
        self.assertIn("unregistered_csv_image", self.codes(self.run_audit([a])))

    def test_product_cannot_be_split_over_csv_parts(self):
        a = self.site("a", 1)
        a["csv_paths"].append("a-copy.csv")
        (self.root / "a-copy.csv").write_bytes((self.root / "a.csv").read_bytes())
        self.assertIn("csv_product_in_multiple_parts", self.codes(self.run_audit([a])))

    def test_expected_product_count_enforced(self):
        a = self.site("a", 1)
        a["expected_products"] = 150
        self.assertIn("product_count_mismatch", self.codes(self.run_audit([a])))

    def test_historical_same_site_requires_explicit_revision(self):
        a = self.site("a", 1)
        self.assertIn("site_id_collision", self.codes(self.run_audit([a], [a])))
        revised = copy.deepcopy(a)
        revised["revision_of"] = "a"
        self.assertEqual(self.run_audit([revised], [a])["exit_code"], 0)

    def test_other_historical_site_duplicate_caught(self):
        a, b = self.site("a", 1), self.site("b", 1)
        self.assertIn("cross_site_product_family", self.codes(self.run_audit([a], [b])))


class URLTests(unittest.TestCase):
    def test_meaningful_image_id_query_preserved(self):
        self.assertNotEqual(public_url("https://example.test/image?id=Ab"), public_url("https://example.test/image?id=ab"))

    def test_product_variant_does_not_change_style_url(self):
        self.assertEqual(product_url("https://www.example.test/products/shirt?variant=1&utm_source=a"), product_url("https://example.test/products/shirt?variant=2"))

    def test_private_image_url_rejected(self):
        self.assertIsNone(public_url("https://example.test/a?token=secret"))
        self.assertIsNone(public_url("https://name:password@example.test/a"))


if __name__ == "__main__":
    unittest.main()
