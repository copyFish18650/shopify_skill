#!/usr/bin/env python3
"""Basic Shopify theme checks and upload ZIP packaging; never performs live actions."""

import argparse
import json
import re
import shutil
import sys
import tempfile
import zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOTS = ("assets", "blocks", "config", "layout", "locales", "sections", "snippets", "templates")
REQUIRED = ("layout/theme.liquid", "templates/index.json", "config/settings_schema.json", "config/settings_data.json")
SKIP_NAMES = {".git", "node_modules", "__pycache__", "__MACOSX", ".DS_Store", "Thumbs.db", "desktop.ini"}
SKIP_SUFFIXES = {".zip", ".bak", ".orig", ".pyc", ".pem", ".key", ".log"}
SCHEMA = re.compile(r"{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}", re.S)
SCHEMA_OPEN = re.compile(r"{%-?\s*schema\s*-?%}")
SCHEMA_CLOSE = re.compile(r"{%-?\s*endschema\s*-?%}")
COMMENTS = re.compile(r"{%-?\s*comment\s*-?%}.*?{%-?\s*endcomment\s*-?%}", re.S)
# Shopify's import/save validator distinguishes an omitted schema default from
# an explicit blank default. This does NOT prohibit blank merchant-saved values.
NONEMPTY_DEFAULT_TYPES = {"text", "textarea", "url", "richtext", "inline_richtext", "html", "liquid", "video_url"}
RICH_TEXT_ROOTS = {"p", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6"}
RICH_TEXT_INLINE = {"a", "b", "strong", "i", "em", "u", "span", "br"}
THEME_METADATA_KEYS = {"theme_name", "theme_author", "theme_version", "theme_documentation_url", "theme_support_email", "theme_support_url"}


class RichTextParser(HTMLParser):
    """Validate static richtext fragments without repairing or rewriting copy.

    Input-setting docs require block-wrapped richtext, not bare text. Shopify's
    saved-value validator also accepts ordered lists and heading root nodes.
    https://shopify.dev/docs/storefronts/themes/architecture/settings/input-settings#richtext
    This is an import preflight, not a complete replacement for Shopify's parser.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.problems = []
        self.roots = 0

    def handle_starttag(self, tag, attrs):
        if not self.stack:
            self.roots += 1
            if tag not in RICH_TEXT_ROOTS:
                self.problems.append(f"top-level <{tag}> is not supported; use p, ul, ol, or h1-h6")
        elif tag not in RICH_TEXT_ROOTS | RICH_TEXT_INLINE | {"li"}:
            self.problems.append(f"unsupported richtext tag <{tag}>")
        parent = self.stack[-1] if self.stack else None
        if parent in {"ul", "ol"} and tag != "li":
            self.problems.append(f"<{parent}> must contain <li> items")
        if tag == "li" and parent not in {"ul", "ol"}:
            self.problems.append("<li> must be inside <ul> or <ol>")
        if parent and parent not in {"li", "ul", "ol"} and tag in RICH_TEXT_ROOTS | {"li"}:
            self.problems.append(f"block <{tag}> cannot be nested inside <{parent}>")
        if tag != "br":
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag != "br":
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.problems.append(f"unexpected closing </{tag}>")
            return
        self.stack.pop()

    def handle_data(self, data):
        if data.strip() and (not self.stack or self.stack[-1] in {"ul", "ol"}):
            self.problems.append("non-whitespace text must be wrapped in a block (and list text in <li>)")

    def handle_decl(self, decl):
        self.problems.append("HTML declarations are not richtext content")

    def handle_pi(self, data):
        self.problems.append("processing instructions are not richtext content")


def check_richtext_value(value, location, errors, allow_translation=False):
    if not isinstance(value, str):
        errors.append(f"{location}: richtext value must be a string")
        return
    stripped = value.strip()
    # Empty saved values are valid. Do not inspect a native dynamic source's
    # unresolved contents as literal HTML, or schema-locale translation keys.
    if not stripped or (stripped.startswith("{{") and stripped.endswith("}}")):
        return
    if allow_translation and stripped.startswith("t:"):
        return
    parser = RichTextParser()
    parser.feed(value)
    parser.close()
    if parser.stack:
        parser.problems.append("unclosed tags: " + ", ".join(parser.stack))
    if not parser.roots:
        parser.problems.append("richtext needs a p, ul, ol, or h1-h6 top-level element")
    if parser.problems:
        errors.append(f"{location}: invalid richtext HTML: " + "; ".join(dict.fromkeys(parser.problems)))


def check_setting_values(fields, values, location, errors, allow_translation=False):
    check_enum_settings(fields, values, location, errors)
    if not isinstance(fields, list) or not isinstance(values, dict):
        return
    for field in fields:
        if not isinstance(field, dict) or field.get("id") not in values:
            continue
        value = values[field["id"]]
        if field.get("type") == "richtext":
            check_richtext_value(value, f"{location}/{field['id']}", errors, allow_translation)


def check_saved_blocks(blocks, definitions, schemas, location, errors, allow_translation=False):
    # Presets use arrays; JSON templates and saved configurations use ID maps.
    items = blocks.items() if isinstance(blocks, dict) else enumerate(blocks) if isinstance(blocks, list) else []
    for block_id, block in items:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        definition = definitions.get(block_type) or schemas.get(f"blocks/{block_type}.liquid", {})
        block_location = f"{location}/{block_id}"
        check_setting_values(definition.get("settings", []), block.get("settings", {}), block_location, errors, allow_translation)
        nested_definitions = {item.get("type"): item for item in definition.get("blocks", []) if isinstance(item, dict)}
        check_saved_blocks(block.get("blocks", {}), nested_definitions, schemas, block_location, errors, allow_translation)


def is_within(path, base):
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError(f"non-finite JSON number: {value}")


def parse_json(source, allow_header=False):
    source = source.lstrip("\ufeff \t\r\n")
    # Shopify exports can begin with generated comments. Do not alter strings/URLs.
    if allow_header:
        while source.startswith(("/*", "//")):
            if source.startswith("/*"):
                end = source.find("*/", 2)
                if end < 0:
                    raise ValueError("unterminated JSON header comment")
                source = source[end + 2:].lstrip()
            else:
                source = source.partition("\n")[2].lstrip()
    return json.loads(source, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def walk_objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_objects(child)


def check_enum_settings(fields, values, location, errors):
    """Check saved/preset values too; disabled sections still undergo import validation."""
    if not isinstance(fields, list) or not isinstance(values, dict):
        return
    for field in fields:
        if not isinstance(field, dict) or field.get("type") not in {"select", "radio"}:
            continue
        key = field.get("id")
        if key not in values:
            continue
        options = field.get("options", [])
        allowed = [item.get("value") for item in options if isinstance(item, dict)] if isinstance(options, list) else []
        value = values[key]
        # A native dynamic-source reference is resolved by Shopify, not this static checker.
        if isinstance(value, str) and value.strip().startswith("{{") and value.strip().endswith("}}"):
            continue
        if value not in allowed:
            errors.append(f"{location}: {key} value {value!r} is not a declared {field['type']} option")


def check_saved_section(section, schemas, location, errors):
    if not isinstance(section, dict):
        return
    schema = schemas.get(f"sections/{section.get('type')}.liquid")
    if not schema:
        return
    check_setting_values(schema.get("settings", []), section.get("settings", {}), location, errors)
    definitions = {block.get("type"): block for block in schema.get("blocks", []) if isinstance(block, dict)}
    check_saved_blocks(section.get("blocks", {}), definitions, schemas, location, errors)


def inspect_theme(root):
    root = Path(root).resolve()
    errors, warnings, files, documents, schemas = [], [], [], {}, {}
    for folder in ROOTS:
        if not (root / folder).is_dir():
            errors.append(f"missing root directory: {folder}/")
    for name in REQUIRED:
        if not (root / name).is_file():
            errors.append(f"missing required file: {name}")
    if (root / "templates/index.liquid").exists():
        errors.append("templates/index.liquid conflicts with required templates/index.json")

    package_roots = list(ROOTS) + (["listings"] if (root / "listings").exists() else [])
    for folder in package_roots:
        base = root / folder
        if base.is_symlink():
            errors.append(f"symlink root is not packaged: {folder}")
            continue
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            relative = path.relative_to(root)
            if path.is_symlink() or not is_within(path.resolve(), root):
                errors.append(f"symlink or escaped path is not packaged: {relative.as_posix()}")
                continue
            if any(part in SKIP_NAMES or part.startswith(".") for part in relative.parts):
                continue
            if not path.is_file():
                continue
            if path.suffix.lower() in SKIP_SUFFIXES:
                warnings.append(f"excluded development/backup file: {relative.as_posix()}")
                continue
            files.append(path)
            try:
                if path.suffix.lower() == ".json":
                    documents[relative.as_posix()] = parse_json(path.read_text(encoding="utf-8-sig"), True)
                if path.suffix.lower() == ".liquid" and relative.parts[0] in {"sections", "blocks"}:
                    source = COMMENTS.sub("", path.read_text(encoding="utf-8-sig"))
                    matches = list(SCHEMA.finditer(source))
                    starts, ends = len(SCHEMA_OPEN.findall(source)), len(SCHEMA_CLOSE.findall(source))
                    if starts != ends or starts != len(matches) or starts > 1:
                        raise ValueError("unbalanced or multiple schema tags")
                    if matches:
                        schema = parse_json(matches[0].group(1))
                        if not isinstance(schema, dict):
                            raise ValueError("schema must be a JSON object")
                        schemas[relative.as_posix()] = schema
            except (OSError, UnicodeError, ValueError) as exc:
                errors.append(f"{relative.as_posix()}: {exc}")

    for name, doc in documents.items():
        if not name.startswith(("templates/", "sections/")):
            continue
        if name == "templates/index.json" and not isinstance(doc, dict):
            errors.append("templates/index.json must be an object")
            continue
        if not isinstance(doc, dict) or "sections" not in doc:
            if name == "templates/index.json":
                errors.append("templates/index.json has no sections")
            continue
        sections, order = doc["sections"], doc.get("order")
        if not isinstance(sections, dict) or not isinstance(order, list):
            errors.append(f"{name}: sections must be an object and order a list")
            continue
        if not all(isinstance(item, str) for item in order):
            errors.append(f"{name}: order IDs must be strings")
            continue
        if len(order) != len(set(order)) or any(item not in sections for item in order):
            errors.append(f"{name}: duplicate or missing section IDs in order")
        if name == "templates/index.json" and not order:
            errors.append("templates/index.json has an empty section order")
        for section_id, section in sections.items():
            # Preserve native generated underscores/hyphens; prose and whitespace are never IDs.
            if not re.fullmatch(r"[A-Za-z0-9_-]+", section_id):
                errors.append(f"{name}: invalid section ID {section_id!r}; no spaces or punctuation")
            section_type = section.get("type") if isinstance(section, dict) else None
            if not isinstance(section_type, str) or not section_type:
                errors.append(f"{name}: section {section_id} has no valid type")
                continue
            if any(character in section_type for character in '/\\:') or section_type in {'.', '..'}:
                errors.append(f"{name}: invalid section file name: {section_type}")
                continue
            if not (root / "sections" / f"{section_type}.liquid").is_file():
                errors.append(f"{name}: missing section file for {section_type}")
            check_saved_section(section, schemas, f"{name}/{section_id}", errors)
            blocks = section.get("blocks", {})
            block_order = section.get("block_order", [])
            if not isinstance(blocks, dict) or not isinstance(block_order, list):
                errors.append(f"{name}: section {section_id} has invalid blocks or block_order")
                continue
            if not all(isinstance(item, str) for item in block_order):
                errors.append(f"{name}: section {section_id} block_order IDs must be strings")
            elif len(block_order) != len(set(block_order)) or any(item not in blocks for item in block_order):
                errors.append(f"{name}: section {section_id} has duplicate or missing block IDs in block_order")
            for block_id in blocks:
                if not re.fullmatch(r"[A-Za-z0-9_-]+", block_id):
                    errors.append(f"{name}: section {section_id} has invalid block ID {block_id!r}; no spaces or punctuation")

    # A valid index does not guarantee that a layout's header/footer groups exist.
    for path in files:
        if path.suffix != ".liquid" or path.relative_to(root).parts[0] != "layout":
            continue
        source = COMMENTS.sub("", path.read_text(encoding="utf-8-sig"))
        for group_name in re.findall(r"{%-?\s*sections\s+['\"]([^'\"]+)['\"]\s*-?%}", source):
            group = documents.get(f"sections/{group_name}.json")
            if not isinstance(group, dict) or not isinstance(group.get("sections"), dict):
                errors.append(f"{path.relative_to(root).as_posix()}: missing section group {group_name}")
                continue
            group_type = group.get("type", "")
            if not isinstance(group_type, str) or not re.fullmatch(r"header|footer|aside|custom\..+", group_type):
                errors.append(f"sections/{group_name}.json: invalid section group type")

    global_schema = documents.get("config/settings_schema.json")
    data = documents.get("config/settings_data.json")
    if not isinstance(global_schema, list):
        errors.append("config/settings_schema.json must be an array")
        global_schema = []
    # Theme metadata is optional, but a metadata object is only recognized under
    # this literal name. Do not require metadata, its position, or invented URLs.
    # https://shopify.dev/docs/storefronts/themes/architecture/config/settings-schema-json#add-theme-metadata
    for panel in global_schema:
        if isinstance(panel, dict) and THEME_METADATA_KEYS.intersection(panel) and panel.get("name") != "theme_info":
            errors.append("config/settings_schema.json: an object with theme_* metadata must have name 'theme_info'; remove misplaced metadata from an ordinary settings category")
    if not isinstance(data, dict):
        errors.append("config/settings_data.json must be an object")
        data = {}
    current = data.get("current")
    if isinstance(current, str):
        presets = data.get("presets", {})
        current = presets.get(current) if isinstance(presets, dict) else None
    if not isinstance(current, dict):
        errors.append("settings_data.current must be an object or resolve to a saved preset")
        current = {}

    global_fields = [field for panel in global_schema if isinstance(panel, dict)
                     for field in panel.get("settings", []) if isinstance(field, dict)]
    saved_presets = data.get("presets", {})
    configurations = [("current", current)]
    if isinstance(saved_presets, dict):
        configurations += [(f"preset/{key}", value) for key, value in saved_presets.items() if isinstance(value, dict)]
    for config_name, config in configurations:
        check_setting_values(global_fields, config, f"settings_data/{config_name}", errors)
        saved_sections = config.get("sections", {})
        if isinstance(saved_sections, dict):
            for section_id, section in saved_sections.items():
                check_saved_section(section, schemas, f"settings_data/{config_name}/{section_id}", errors)

    groups = [obj for obj in walk_objects(global_schema) if obj.get("type") == "color_scheme_group"]
    if not groups:
        errors.append("no native color_scheme_group definition in settings_schema.json")
    for group in groups:
        group_id = group.get("id")
        if not isinstance(group_id, str):
            errors.append("color_scheme_group has no valid id")
            continue
        if not isinstance(group.get("definition"), list) or not group["definition"]:
            errors.append(f"color scheme group {group_id} has no definition fields")
        schemes = current.get(group_id)
        if not isinstance(schemes, dict) or not schemes:
            errors.append(f"no saved color schemes for schema group {group_id}")
            continue
        for scheme_id, scheme in schemes.items():
            if not isinstance(scheme, dict) or not isinstance(scheme.get("settings"), dict):
                errors.append(f"invalid color scheme settings object: {group_id}.{scheme_id}")

    # Scope uniqueness to each settings/definition array, not across independent blocks.
    for name, doc in [("config/settings_schema.json", global_schema), *schemas.items()]:
        for obj in walk_objects(doc):
            if obj.get("type") in {"select", "radio"} and "default" in obj:
                check_enum_settings([obj], {obj.get("id"): obj["default"]}, f"{name}/default", errors)
            if obj.get("type") in NONEMPTY_DEFAULT_TYPES and "id" in obj and "default" in obj:
                default = obj["default"]
                if isinstance(default, str) and not default.strip():
                    errors.append(f"{name}: {obj['type']} {obj['id']} has an explicit blank schema default; omit the default attribute for an optional empty field (saved values may remain empty)")
                elif obj["type"] == "richtext":
                    check_richtext_value(default, f"{name}/default/{obj['id']}", errors, allow_translation=True)
            if obj.get("type") == "inline_richtext" and isinstance(obj.get("default"), str):
                if re.search(r"<\s*br\b", obj["default"], re.I):
                    errors.append(f"{name}: inline_richtext {obj.get('id')} default contains unsupported line breaks")
            for key in ("settings", "definition"):
                settings = obj.get(key)
                if not isinstance(settings, list):
                    continue
                ids = [setting["id"] for setting in settings if isinstance(setting, dict) and isinstance(setting.get("id"), str)]
                if len(ids) != len(set(ids)):
                    errors.append(f"{name}: duplicate setting IDs in one {key} array")
    for name, doc in schemas.items():
        # Native Shopify save validation rejects two menu pickers in one scope.
        # Separate blocks can each have a menu; never count across all blocks.
        scopes = [("section", doc), *((block.get("type", "block"), block) for block in doc.get("blocks", []))]
        for scope_name, scope in scopes:
            settings = scope.get("settings", [])
            if isinstance(settings, list) and sum(isinstance(item, dict) and item.get("type") == "link_list" for item in settings) > 1:
                errors.append(f"{name}: {scope_name} settings contain multiple link_list pickers; use separate menu blocks")
        for item in [doc, *doc.get("blocks", []), *doc.get("presets", [])]:
            label = item.get("name", "")
            if isinstance(label, str) and not label.startswith("t:") and len(label) > 25:
                errors.append(f"{name}: section/block/preset name exceeds conservative 25-character limit: {label}")
        for preset in doc.get("presets", []):
            check_setting_values(doc.get("settings", []), preset.get("settings", {}), f"{name}/preset", errors, allow_translation=True)
            definitions = {block.get("type"): block for block in doc.get("blocks", []) if isinstance(block, dict)}
            check_saved_blocks(preset.get("blocks", []), definitions, schemas, f"{name}/preset", errors, allow_translation=True)

    return {
        "static_passed": not errors,
        "runtime_verified": False,
        "json_files": len(documents),
        "liquid_schemas": len(schemas),
        "errors": errors,
        "warnings": warnings,
        "limits": "Basic static checks only; run official Theme Check and preview functional/visual tests.",
    }, files, package_roots


def package_theme(root, files, package_roots, destination, max_bytes):
    if is_within(destination, root):
        raise ValueError("ZIP output must be outside the theme directory")
    if destination.exists():
        raise ValueError("ZIP destination already exists; choose a new name")
    with tempfile.TemporaryFile() as buffer:
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for folder in package_roots:
                archive.writestr(f"{folder}/", b"")
            for path in files:
                archive.write(path, path.relative_to(root).as_posix())
        size = buffer.tell()
        if size >= max_bytes:
            raise ValueError(f"ZIP is {size} bytes; must be strictly below {max_bytes}")
        buffer.seek(0)
        with zipfile.ZipFile(buffer) as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP CRC check failed")
            names = set(archive.namelist())
            if any(f"{folder}/" not in names for folder in ROOTS) or not set(REQUIRED).issubset(names):
                raise ValueError("ZIP root structure is incomplete")
        destination.parent.mkdir(parents=True, exist_ok=True)
        buffer.seek(0)
        with destination.open("xb") as target:
            shutil.copyfileobj(buffer, target)
    return {"path": str(destination), "bytes": size, "crc_verified": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("theme_dir", type=Path)
    parser.add_argument("--zip", dest="zip_path", type=Path)
    parser.add_argument("--max-bytes", type=int, default=50_000_000)
    args = parser.parse_args()
    root = args.theme_dir.resolve()
    if not root.is_dir() or args.max_bytes <= 0:
        parser.error("theme_dir must be a directory and max-bytes must be positive")
    try:
        report, files, package_roots = inspect_theme(root)
        if args.zip_path and report["static_passed"]:
            report["zip"] = package_theme(root, files, package_roots, args.zip_path.resolve(), args.max_bytes)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["static_passed"] else 1
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(json.dumps({"error": str(exc), "runtime_verified": False}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
