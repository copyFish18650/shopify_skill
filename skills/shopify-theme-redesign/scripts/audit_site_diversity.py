#!/usr/bin/env python3
"""Audit explicitly supplied local site manifests; never scan folders or fetch URLs.

Exit 0: submitted scope has no errors or pending review flags.
Exit 1: invalid evidence, cross-site exact marketing image reuse, or identical design.
Exit 2: human visual review is needed. Review findings are not exact-duplicate proof.

Manifest paths are relative to the manifest file. History uses the same schema as
the plan. Optional site ``revision_of`` must equal its site_id to explicitly mark
a continuation of a historical site. Optional image ``responsive_group`` marks
same-site responsive renditions of a single placement. Neither allows cross-site
image reuse. Design reference locks are explicit component names, with a nonempty
``reference_lock_reason``; the caller must obtain actual user authorization.
"""

import argparse
import hashlib
import json
import re
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = ImageOps = None


MARKETING_ROLES = frozenset({"hero", "carousel", "lifestyle", "category", "editorial"})
EXCLUDED_ROLES = frozenset({"product", "pdp"})
DESIGN_AXES = (
    "hero_composition", "navigation_structure", "section_rhythm",
    "category_presentation", "product_card", "typography", "surface_structure",
    "collection_layout", "product_layout", "interactions",
)
STRUCTURE_AXES = ("hero_composition", "navigation_structure", "section_rhythm", "product_card")
TRANSFORM_PARAMS = frozenset({
    "w", "h", "width", "height", "fit", "crop", "quality", "q", "format", "fm",
    "auto", "dpr", "resize", "rect", "pad", "bg", "cs", "orient",
})
IMAGE_CDN_HOSTS = frozenset({
    "cdn.shopify.com", "images.unsplash.com", "plus.unsplash.com", "images.pexels.com",
})
TRACKING_PARAMS = frozenset({"fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid", "igshid"})
# These fields must never appear in the report, including when an input URL is signed.
SECRET_PARAMS = frozenset({
    "token", "access_token", "auth", "authorization", "key", "api_key", "apikey",
    "signature", "sig", "expires", "policy", "credential", "password", "secret",
})
SHOPIFY_SIZE = re.compile(
    r"_(?:\d+x\d*|x\d+)(?:_crop_(?:center|top|bottom|left|right))?(?:@\d+x)?(?=\.[^.]+$)",
    re.IGNORECASE,
)
DHASH_DISTANCE = 6  # A candidate-review heuristic only, never evidence of a duplicate.


def canonical_source(value):
    """Keep semantic identity query fields; normalize documented CDN transforms."""
    value = str(value).strip()
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return value
    host = (parsed.hostname or "").lower()
    try:
        port = parsed.port
    except ValueError:
        port = None
    authority = host + (":" + str(port) if port and port not in {80, 443} else "")
    path = parsed.path
    shopify_image = host == "cdn.shopify.com" or path.startswith("/cdn/shop/")
    image_cdn = shopify_image or host in IMAGE_CDN_HOSTS
    if shopify_image:
        filename = path.rsplit("/", 1)[-1]
        path = path[:-len(filename)] + SHOPIFY_SIZE.sub("", filename) if filename else path
    query = []
    for key, item in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.casefold()
        if ((image_cdn and lowered in TRANSFORM_PARAMS) or lowered in TRACKING_PARAMS
                or lowered in SECRET_PARAMS or lowered.startswith(("utm_", "x-amz-", "x-goog-"))):
            continue
        # Case-normalize names, not values: id=Ab and id=ab can identify distinct assets.
        query.append((lowered, item))
    return urlunsplit(("https", authority, path, urlencode(sorted(query)), ""))


def clean_identity(value):
    if not isinstance(value, str) or not value.strip():
        return None
    return canonical_source(value)


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pixel_fingerprints(path):
    """Hash decoded, EXIF-oriented full RGB pixels, then a review-only 64-bit dHash.

    No resize/crop enters the exact hash. Lossy re-encoding usually changes pixels
    and may only be identified as a perceptual candidate. Alpha is composited on
    white to make the displayed RGB rendition explicit.
    """
    with Image.open(path) as opened:
        frame = ImageOps.exif_transpose(opened)
        if "A" in frame.getbands() or "transparency" in frame.info:
            rgba = frame.convert("RGBA")
            rgb = Image.new("RGB", rgba.size, "white")
            rgb.paste(rgba, mask=rgba.getchannel("A"))
        else:
            rgb = frame.convert("RGB")
        payload = struct.pack(">II", *rgb.size) + rgb.tobytes()
        exact = hashlib.sha256(payload).hexdigest()
        resampling = getattr(Image, "Resampling", Image)
        gray = rgb.convert("L").resize((9, 8), resampling.LANCZOS)
        pixels = list(gray.getdata())
        dhash = 0
        for row in range(8):
            for col in range(8):
                dhash = (dhash << 1) | (pixels[row * 9 + col] > pixels[row * 9 + col + 1])
        return exact, dhash, list(rgb.size), getattr(opened, "n_frames", 1) > 1


def normalized_design(value):
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value.strip()).casefold() or None
    if isinstance(value, list) and value:
        result = [normalized_design(item) for item in value]
        return result if all(item is not None for item in result) else None
    if isinstance(value, dict) and value:
        result = {str(key).casefold(): normalized_design(item) for key, item in value.items()}
        return result if all(item is not None for item in result.values()) else None
    return None


def endpoint(image):
    return {key: image[key] for key in ("manifest", "scope", "site_id", "role", "path", "image_index")}


class Audit:
    def __init__(self):
        self.findings = []
        self.manifests = []
        self.sites = []
        self.images = []
        self.design_comparisons = []
        self.same_site_revisions = []
        self.reference_exemptions = []

    def finding(self, severity, code, message, **details):
        self.findings.append({"severity": severity, "code": code, "message": message, **details})

    def read_manifest(self, path, scope):
        manifest = {"path": str(path), "scope": scope, "loaded": False, "sites": 0,
                    "marketing_images_declared": 0, "marketing_images_hashed": 0, "excluded_product_images": 0}
        self.manifests.append(manifest)
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as error:
            self.finding("error", "manifest_unreadable", f"Cannot load {scope} manifest ({type(error).__name__}).", manifest=str(path))
            return
        if not isinstance(data, dict) or not isinstance(data.get("sites"), list) or not data["sites"]:
            self.finding("error", "manifest_schema", "Manifest needs a nonempty sites array.", manifest=str(path))
            return
        manifest["loaded"] = True
        seen = set()
        for site_index, raw_site in enumerate(data["sites"]):
            context = {"manifest": str(path), "site_index": site_index}
            if not isinstance(raw_site, dict) or not isinstance(raw_site.get("site_id"), str) or not raw_site["site_id"].strip():
                self.finding("error", "site_id_missing", "Each site needs a nonempty string site_id.", **context)
                continue
            site_id = raw_site["site_id"].strip()
            if site_id in seen:
                self.finding("error", "duplicate_site_id", "A site_id appears more than once in one manifest.", site_id=site_id, **context)
            seen.add(site_id)
            revision = raw_site.get("revision_of")
            if revision is not None and revision != site_id:
                self.finding("error", "invalid_revision", "revision_of must equal site_id; a different site cannot be relabeled as a revision.", site_id=site_id, **context)
            design = raw_site.get("design")
            design = design if isinstance(design, dict) else {}
            axes = {axis: normalized_design(design.get(axis)) for axis in DESIGN_AXES}
            if not isinstance(design.get("interactions"), list):
                axes["interactions"] = None
            if isinstance(axes["interactions"], list):
                axes["interactions"] = sorted(axes["interactions"], key=lambda item: json.dumps(item, sort_keys=True))
            missing = [axis for axis, value in axes.items() if value is None]
            if missing:
                self.finding("review", "incomplete_design", "Design evidence is incomplete; visual diversity cannot be certified.", site_id=site_id, missing_axes=missing, **context)
            locks = design.get("locked_reference_components", [])
            if not isinstance(locks, list) or any(not isinstance(item, str) or item not in DESIGN_AXES for item in locks):
                self.finding("error", "invalid_reference_locks", "locked_reference_components must list known design axes.", site_id=site_id, **context)
                locks = []
            reason = design.get("reference_lock_reason")
            if locks and (not isinstance(reason, str) or not reason.strip()):
                self.finding("error", "reference_lock_reason_missing", "Reference locks require an explicit reference_lock_reason based on user instructions.", site_id=site_id, **context)
                locks = []
            site = {"site_id": site_id, "manifest": str(path), "scope": scope,
                    "revision_of": revision, "design": axes, "complete_design": not missing,
                    "locks": set(locks), "has_lock_reason": bool(reason)}
            self.sites.append(site)
            manifest["sites"] += 1
            raw_images = raw_site.get("images")
            if not isinstance(raw_images, list):
                self.finding("error", "images_schema", "Each site needs an images array.", site_id=site_id, **context)
                continue
            marketing_count = 0
            for index, raw in enumerate(raw_images):
                image_context = {"manifest": str(path), "site_id": site_id, "image_index": index}
                if not isinstance(raw, dict) or not isinstance(raw.get("role"), str) or raw["role"] not in MARKETING_ROLES | EXCLUDED_ROLES:
                    self.finding("error", "unsupported_image_role", "Image role must be hero, carousel, lifestyle, category, editorial, product, or pdp.", **image_context)
                    continue
                role = raw["role"]
                if role in EXCLUDED_ROLES:
                    manifest["excluded_product_images"] += 1
                    continue
                marketing_count += 1
                manifest["marketing_images_declared"] += 1
                raw_path = raw.get("path")
                if not isinstance(raw_path, str) or not raw_path.strip():
                    self.finding("error", "image_path_missing", "Every marketing image needs an existing local path for SHA256.", role=role, **image_context)
                    continue
                try:
                    image_path = Path(raw_path)
                    if not image_path.is_absolute():
                        image_path = path.parent / image_path
                    image_path = image_path.resolve()
                except (OSError, ValueError) as error:
                    self.finding("error", "image_path_invalid", f"Cannot resolve marketing image path ({type(error).__name__}).", role=role, **image_context)
                    continue
                image = {"manifest": str(path), "scope": scope, "site": site, "site_id": site_id,
                         "role": role, "path": str(image_path), "image_index": index,
                         "sources": set(), "sha256": None, "pixel_sha256": None, "dhash": None,
                         "responsive_group": clean_identity(raw.get("responsive_group"))}
                for field in ("source_id", "source_url", "parent_source_id"):
                    identity = clean_identity(raw.get(field))
                    if identity:
                        image["sources"].add(identity)
                if not image["sources"]:
                    self.finding("review", "source_provenance_missing", "Source identity is missing; transformed renditions need source review.", image=endpoint(image))
                try:
                    image["sha256"] = sha256_file(image_path)
                    manifest["marketing_images_hashed"] += 1
                except OSError as error:
                    self.finding("error", "image_unreadable", f"Cannot hash marketing image ({type(error).__name__}).", image=endpoint(image))
                if Image is not None and image["sha256"]:
                    try:
                        exact, dhash, dimensions, animated = pixel_fingerprints(image_path)
                        image.update(pixel_sha256=exact, dhash=dhash, dimensions=dimensions)
                        if animated:
                            self.finding("review", "animated_image_partial", "Only the first animation frame was fingerprinted; review all frames.", image=endpoint(image))
                    except (OSError, ValueError, SyntaxError) as error:
                        self.finding("review", "pixel_decode_unavailable", f"Decoded image checks could not run ({type(error).__name__}).", image=endpoint(image))
                self.images.append(image)
            if not marketing_count:
                self.finding("review", "incomplete_image_scope", "No marketing images were declared; this is partial evidence, not a complete image-reuse check.", site_id=site_id, **context)

    def same_site(self, left, right):
        if left is right:
            return True
        if left["site_id"] != right["site_id"]:
            return False
        current, old = (left, right) if left["scope"] == "plan" else (right, left)
        return current["scope"] == "plan" and old["scope"] == "history" and current["revision_of"] == current["site_id"]

    @staticmethod
    def compare_pair(left, right):
        return left["scope"] == "plan" or right["scope"] == "plan"

    def compare_sites(self):
        for index, left in enumerate(self.sites):
            for right in self.sites[index + 1:]:
                if not self.compare_pair(left, right):
                    continue
                pair = [{"site_id": site["site_id"], "manifest": site["manifest"], "scope": site["scope"]} for site in (left, right)]
                if left["site_id"] == right["site_id"]:
                    if self.same_site(left, right):
                        self.same_site_revisions.append({"sites": pair, "basis": "plan revision_of explicitly equals historical site_id"})
                    else:
                        self.finding("error", "duplicate_site_identity", "The same site_id occurs in different site records without an explicit same-site revision.", sites=pair)
                    continue
                shared = [axis for axis in DESIGN_AXES if left["design"][axis] is not None and left["design"][axis] == right["design"][axis]]
                different = [axis for axis in DESIGN_AXES if left["design"][axis] is not None and right["design"][axis] is not None and axis not in shared]
                self.design_comparisons.append({"sites": pair, "matching_axes": shared, "different_axes": different,
                                                "both_complete": left["complete_design"] and right["complete_design"]})
                unlocked_shared = [axis for axis in shared if axis not in left["locks"] or axis not in right["locks"]]
                if len(shared) == len(DESIGN_AXES):
                    if not unlocked_shared:
                        self.reference_exemptions.append({"sites": pair, "axes": list(DESIGN_AXES), "basis": "Both records explicitly lock every axis with a reference_lock_reason; user authorization must be verified separately."})
                    else:
                        self.finding("error", "identical_design_signature", "Different sites have the same complete design signature. Changing photographs or colors alone does not resolve this finding.", sites=pair, unlocked_matching_axes=unlocked_shared)
                elif all(axis in shared for axis in STRUCTURE_AXES) and any(axis in unlocked_shared for axis in STRUCTURE_AXES):
                    self.finding("review", "similar_design_structure", "Hero, navigation, section rhythm, and product-card descriptions match; inspect whole-page desktop/mobile screenshots. This heuristic is not a visual quality score.", sites=pair, matching_axes=shared, different_axes=different)

    def compare_images(self):
        for index, left in enumerate(self.images):
            for right in self.images[index + 1:]:
                if not self.compare_pair(left, right):
                    continue
                same_site = self.same_site(left["site"], right["site"])
                # Different revisions of the same explicitly identified site are not new placements.
                if same_site and left["site"] is not right["site"]:
                    continue
                evidence = []
                if left["sources"] & right["sources"]:
                    evidence.append("canonical_source")
                if left["sha256"] and left["sha256"] == right["sha256"]:
                    evidence.append("sha256")
                if left["pixel_sha256"] and left["pixel_sha256"] == right["pixel_sha256"]:
                    evidence.append("decoded_rgb_sha256")
                pair = [endpoint(left), endpoint(right)]
                if evidence:
                    if not same_site:
                        self.finding("error", "cross_site_image_reuse", "Different sites reuse an exact marketing image or canonical source.", images=pair, evidence=evidence)
                    elif (left["responsive_group"] and left["responsive_group"] == right["responsive_group"]):
                        continue
                    elif left["role"] in {"hero", "carousel"} or right["role"] in {"hero", "carousel"}:
                        self.finding("review", "same_site_repeated_marketing_source", "A source repeats in same-site hero/carousel placements. Review slide repetition; explicitly group genuine responsive renditions with responsive_group.", images=pair, evidence=evidence, severity_note="warning for manual review; not cross-site reuse")
                    continue
                if left["dhash"] is not None and right["dhash"] is not None:
                    distance = bin(left["dhash"] ^ right["dhash"]).count("1")
                    if distance <= DHASH_DISTANCE:
                        if same_site and left["responsive_group"] and left["responsive_group"] == right["responsive_group"]:
                            continue
                        self.finding("review", "perceptual_similarity_candidate", "Perceptual similarity is a candidate for human visual review, not proof of image reuse. Check recompression, alternate crops, and genuinely different photographs.", images=pair, dhash_hamming_distance=distance)

    def report(self):
        errors = sum(item["severity"] == "error" for item in self.findings)
        reviews = sum(item["severity"] == "review" for item in self.findings)
        return {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "fail" if errors else "needs_review" if reviews else "pass",
            "exit_code": 1 if errors else 2 if reviews else 0,
            "counts": {"errors": errors, "review_flags": reviews, "sites_loaded": len(self.sites),
                       "marketing_images_declared": sum(item["marketing_images_declared"] for item in self.manifests),
                       "marketing_images_hashed": sum(item["marketing_images_hashed"] for item in self.manifests)},
            "scope": {"basis": "Only supplied plan/history manifests and declared local files; no discovery, network requests, or global registry.",
                      "manifests": self.manifests, "historical_manifests_supplied": sum(item["scope"] == "history" for item in self.manifests),
                      "historical_manifests_loaded": sum(item["scope"] == "history" and item["loaded"] for item in self.manifests),
                      "historical_sites_loaded": sum(site["scope"] == "history" for site in self.sites),
                      "same_site_revisions": self.same_site_revisions,
                      "history_to_history_checked": False},
            "capabilities": {"sha256": True, "decoded_rgb_exact": Image is not None, "dhash_review_candidates": Image is not None,
                             "dhash_review_distance": DHASH_DISTANCE},
            "findings": self.findings,
            "design_comparisons": self.design_comparisons,
            "explicit_reference_exemptions": self.reference_exemptions,
            "limitations": [
                "A pass covers only declared evidence, not all past sites or undeclared page images. Missing history is never treated as a full-history check.",
                "Product/PDP media is excluded unless declared in a marketing role. Manifests cannot prove that every actual marketing placement is represented.",
                "Source identity normalization removes resize/crop/quality fields only on cdn.shopify.com, /cdn/shop/ paths, images.unsplash.com, plus.unsplash.com, and images.pexels.com. Ordinary source-page query fields, including q/w/h, remain identity-bearing. Tracking/signing fields are removed everywhere; semantic image/id/color/version fields remain. Incorrect source metadata can cause false positives or missed reuse.",
                "Decoded RGB exact hashes detect identical displayed pixels, including lossless re-encoding; lossy recompression, resizing, crops, and edits are not guaranteed exact matches.",
                "dHash only flags candidates, can miss crops or different variants, and can match unrelated images. It never certifies distinctness or a pixel-level duplicate.",
                "Design signatures and overlap warnings guide screenshot review; there is no automatic premium-quality score or numeric diversity pass threshold.",
                "Manual visual review and its decision must be recorded in local project evidence; this tool does not auto-clear pending review flags.",
                "Reference locks are declarations that require actual explicit user instruction, not inferred permission from a source URL or mode.",
            ],
        }


def run(plan, histories):
    audit = Audit()
    audit.read_manifest(Path(plan).resolve(), "plan")
    history_paths = set()
    for history in histories:
        path = Path(history).resolve()
        if path in history_paths or path == Path(plan).resolve():
            audit.finding("error", "duplicate_manifest_argument", "History manifests must be distinct from the plan and each other.", manifest=str(path))
            continue
        history_paths.add(path)
        audit.read_manifest(path, "history")
    if Image is None:
        audit.finding("review", "pillow_unavailable", "Pillow is unavailable: decoded RGB and perceptual candidates were not checked. Perform and record visual review; SHA256/source checks still run.")
    audit.compare_sites()
    audit.compare_images()
    return audit.report()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plan", required=True, type=Path, help="Current batch manifest (JSON).")
    parser.add_argument("--history", action="append", default=[], type=Path, help="Explicit historical manifest; repeat for each supplied work record.")
    parser.add_argument("--report", required=True, type=Path, help="Local JSON report path. This file must not overwrite a supplied manifest or image.")
    args = parser.parse_args(argv)
    report = run(args.plan, args.history)
    report_path = args.report.resolve()
    reserved = {args.plan.resolve(), *(path.resolve() for path in args.history)}
    # Protect all referenced files, including product/PDP files that are not fingerprinted.
    for manifest in report["scope"]["manifests"]:
        try:
            data = json.loads(Path(manifest["path"]).read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict) or not isinstance(data.get("sites"), list):
                continue
            for site in data["sites"]:
                if isinstance(site, dict) and isinstance(site.get("images"), list):
                    for item in site["images"]:
                        if isinstance(item, dict) and isinstance(item.get("path"), str):
                            path = Path(item["path"])
                            reserved.add((path if path.is_absolute() else Path(manifest["path"]).parent / path).resolve())
        except (OSError, ValueError, AttributeError):
            continue
    if report_path in reserved:
        parser.error("--report must not overwrite a manifest or declared image")
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as error:
        print(f"Cannot write report ({type(error).__name__}).", file=sys.stderr)
        return 1
    print(f"{report['status']}: {report['counts']['errors']} error(s), {report['counts']['review_flags']} review flag(s). Report: {report_path}")
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
