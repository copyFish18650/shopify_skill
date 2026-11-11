"""Behavioral import regressions: schema defaults differ from saved values."""

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import theme_audit


class ThemeImportSchemaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "theme"
        for folder in theme_audit.ROOTS:
            (self.root / folder).mkdir(parents=True)
        self.global_schema = [{"name": "Brand", "settings": [
            {"type": "text", "id": "tagline", "label": "Tagline"},
            {"type": "richtext", "id": "copy", "label": "Copy"},
            {"type": "color_scheme_group", "id": "color_schemes", "definition": [
                {"type": "color", "id": "background", "label": "Background", "default": "#ffffff"}
            ]}
        ]}]
        self.data = {"current": {"tagline": "", "copy": "", "color_schemes": {"base": {"settings": {"background": "#ffffff"}}}}, "presets": {}}
        self.schema = {"name": "FAQ", "settings": [
            {"type": "text", "id": "eyebrow", "label": "Eyebrow"},
            {"type": "richtext", "id": "text", "label": "Text", "default": "<p>Frequently asked questions.</p>"},
            {"type": "textarea", "id": "plain", "label": "Plain text"},
            {"type": "select", "id": "layout", "label": "Layout", "options": [{"value": "stack", "label": "Stack"}], "default": "stack"}
        ], "blocks": [{"type": "question", "name": "Question", "settings": [
            {"type": "richtext", "id": "answer", "label": "Answer"}
        ]}], "presets": [{"name": "FAQ", "settings": {"eyebrow": "", "text": ""}, "blocks": [{"type": "question", "settings": {"answer": ""}}]}]}
        self.section = {"type": "faq", "settings": {"eyebrow": "", "text": "", "plain": "not HTML", "layout": "stack"}, "blocks": {"question1": {"type": "question", "settings": {"answer": ""}}}, "block_order": ["question1"]}
        self.index = {"sections": {"faq": self.section}, "order": ["faq"]}
        self.layout = "{{ content_for_header }}{{ content_for_layout }}"

    def tearDown(self):
        self.tmp.cleanup()

    def write_json(self, name, value):
        (self.root / name).write_text(json.dumps(value), encoding="utf-8")

    def write_fixture(self):
        self.write_json("config/settings_schema.json", self.global_schema)
        self.write_json("config/settings_data.json", self.data)
        self.write_json("templates/index.json", self.index)
        (self.root / "layout/theme.liquid").write_text(self.layout, encoding="utf-8")
        (self.root / "sections/faq.liquid").write_text("{% schema %}" + json.dumps(self.schema) + "{% endschema %}", encoding="utf-8")

    def audit(self):
        self.write_fixture()
        return theme_audit.inspect_theme(self.root)[0]

    def assert_passes(self):
        report = self.audit()
        self.assertTrue(report["static_passed"], report["errors"])

    def assert_error(self, *fragments):
        report = self.audit()
        self.assertFalse(report["static_passed"])
        for fragment in fragments:
            self.assertTrue(any(fragment in message for message in report["errors"]), report["errors"])

    def test_optional_schema_defaults_and_empty_saved_values_pass(self):
        self.assert_passes()

    def test_explicit_blank_schema_defaults_fail_without_prohibiting_saved_blanks(self):
        for setting_type in sorted(theme_audit.NONEMPTY_DEFAULT_TYPES):
            for blank in ["", " \t\n"]:
                with self.subTest(setting_type=setting_type, blank=repr(blank)):
                    self.schema["settings"][0] = {"type": setting_type, "id": "eyebrow", "label": "Eyebrow", "default": blank}
                    self.assert_error("explicit blank schema default", "omit the default attribute")

    def test_global_and_block_defaults_are_also_checked(self):
        self.global_schema[0]["settings"][0]["default"] = ""
        self.schema["blocks"][0]["settings"][0]["default"] = ""
        self.assert_error("config/settings_schema.json", "richtext answer has an explicit blank")

    def test_saved_richtext_bare_text_fails_even_in_disabled_home_section(self):
        self.section["disabled"] = True
        self.section["settings"]["text"] = "This was accepted as textarea before the schema changed."
        self.assert_error("templates/index.json/faq/text", "invalid richtext HTML")

    def test_textarea_keeps_merchant_plain_text_and_blank_values(self):
        self.schema["settings"][1]["type"] = "textarea"
        self.section["settings"]["text"] = "A normal paragraph without HTML."
        self.assert_passes()

    def test_saved_richtext_accepts_paragraphs_lists_headings_and_entities(self):
        self.section["settings"]["text"] = '<h2>Care &amp; use</h2><p>Use <strong>gently</strong><br />Read <a href="/pages/help">help</a>.</p><ol><li>First</li><li><p>Second</p><ul><li>Detail</li></ul></li></ol>'
        self.assert_passes()

    def test_richtext_rejects_unsupported_root_broken_nesting_and_trailing_text(self):
        for value in ["<div>Copy</div>", "<p>Copy</p>tail", "<p><strong>Copy</p>", "<p>Copy", "<ul>bare list</ul>", "<p><h2>Nested heading</h2></p>"]:
            with self.subTest(value=value):
                self.section["settings"]["text"] = value
                self.assert_error("templates/index.json/faq/text", "invalid richtext HTML")

    def test_schema_richtext_default_and_presets_use_the_referenced_type(self):
        self.schema["settings"][1]["default"] = "bare schema copy"
        self.schema["presets"][0]["settings"]["text"] = "bare preset copy"
        self.schema["presets"][0]["blocks"][0]["settings"]["answer"] = "bare answer"
        self.assert_error("default/text", "sections/faq.liquid/preset/text", "sections/faq.liquid/preset/0/answer")

    def test_saved_local_blocks_are_checked(self):
        self.section["blocks"]["question1"]["settings"]["answer"] = "bare answer"
        self.assert_error("templates/index.json/faq/question1/answer")

    def test_section_group_saved_richtext_is_checked(self):
        self.write_fixture()
        group_section = copy.deepcopy(self.section)
        group_section["settings"]["text"] = "plain group copy"
        self.write_json("sections/footer-group.json", {"type": "footer", "sections": {"footer": group_section}, "order": ["footer"]})
        report = theme_audit.inspect_theme(self.root)[0]
        self.assertTrue(any("sections/footer-group.json/footer/text" in error for error in report["errors"]), report)

    def test_saved_global_current_preset_and_static_sections_are_checked(self):
        self.data["current"]["copy"] = "plain global copy"
        preset = copy.deepcopy(self.data["current"])
        preset["sections"] = {"faq": copy.deepcopy(self.section)}
        preset["sections"]["faq"]["settings"]["text"] = "plain static section copy"
        self.data["presets"]["alternate"] = preset
        self.assert_error("settings_data/current/copy", "settings_data/preset/alternate/copy", "settings_data/preset/alternate/faq/text")

    def test_theme_block_references_and_nested_saved_blocks_are_checked(self):
        self.schema["blocks"] = [{"type": "@theme"}]
        self.section["blocks"]["question1"] = {"type": "group", "blocks": {"answer1": {"type": "answer", "settings": {"copy": "bare nested answer"}}}}
        (self.root / "blocks/group.liquid").write_text('{% schema %}{"name":"Group","blocks":[{"type":"@theme"}]}{% endschema %}', encoding="utf-8")
        (self.root / "blocks/answer.liquid").write_text('{% schema %}{"name":"Answer","settings":[{"type":"richtext","id":"copy","label":"Copy"}]}{% endschema %}', encoding="utf-8")
        self.assert_error("templates/index.json/faq/question1/answer1/copy")

    def test_native_dynamic_sources_and_schema_locale_references_are_not_literal_html(self):
        self.section["settings"]["text"] = "{{ product.metafields.custom.summary }}"
        self.schema["settings"][1]["default"] = "t:sections.faq.copy"
        self.schema["presets"][0]["settings"]["text"] = "t:sections.faq.copy"
        self.assert_passes()

    def test_metadata_optional_but_misnamed_metadata_object_fails(self):
        self.global_schema[0]["theme_name"] = "Store"
        self.assert_error("must have name 'theme_info'")
        self.global_schema[0].pop("theme_name")
        self.assert_passes()

    def test_existing_enum_and_structure_validation_remain_active(self):
        self.section["settings"]["layout"] = "undeclared"
        self.index["order"].append("missing")
        self.assert_error("not a declared select option", "duplicate or missing section IDs")

    def test_failed_preflight_does_not_rewrite_copy_or_create_zip(self):
        self.section["settings"]["text"] = "Do not silently wrap or change merchant copy."
        self.write_fixture()
        paths = [path for path in self.root.rglob("*") if path.is_file()]
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        destination = self.root.parent / "must-not-exist.zip"
        run = subprocess.run([sys.executable, str(Path(theme_audit.__file__)), str(self.root), "--zip", str(destination)], capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertFalse(destination.exists())
        self.assertFalse(json.loads(run.stdout)["static_passed"])
        self.assertEqual(before, {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})


if __name__ == "__main__":
    unittest.main()
