#!/usr/bin/env python3
"""Read-only, explicit-manifest catalog/photo duplicate audit. No network or edits.

0 = no automatic blockers or pending review in submitted evidence; 1 = errors;
2 = missing evidence or perceptual review. Never certifies independent styles,
permission, licensing or actual Shopify import on the basis of hashes alone.
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from audit_site_diversity import canonical_source, sha256_file, pixel_fingerprints, Image


def public_url(value):
    if not isinstance(value, str):
        return None
    try:
        parts = urlsplit(value.strip())
        if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
            return None
        for key, _ in parse_qsl(parts.query):
            if key.lower() in ("token", "access_token", "password", "signature", "sig", "key"):
                return None
        return canonical_source(value)
    except ValueError:
        return None


def product_url(value):
    value = public_url(value)
    if not value:
        return None
    parts = urlsplit(value)
    query = parse_qsl(parts.query, keep_blank_values=True)
    if "/products/" in parts.path:
        query = [(k, v) for k, v in query if k.lower() != "variant"]
    host = parts.netloc.removeprefix("www.") if hasattr(str, "removeprefix") else parts.netloc[4:] if parts.netloc.startswith("www.") else parts.netloc
    return urlunsplit(("https", host, parts.path.rstrip("/"), urlencode(query), ""))


class Audit:
    def __init__(self):
        self.findings = []
        self.products = []
        self.images = []
        self.sites = []
        self.fingerprints = {}

    def finding(self, severity, code, **details):
        self.findings.append(dict(severity=severity, code=code, **details))

    def read(self, path, scope="plan"):
        path = Path(path).resolve()
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            raw_sites = data["sites"]
            if not isinstance(raw_sites, list) or not raw_sites:
                raise ValueError("empty sites")
        except (OSError, ValueError, KeyError, TypeError):
            self.finding("error", "invalid_manifest", manifest=str(path))
            return
        seen = set()
        for raw in raw_sites:
            sid = raw.get("site_id") if isinstance(raw, dict) else None
            if not isinstance(sid, str) or not sid.strip():
                self.finding("error", "missing_site_id", manifest=str(path))
                continue
            sid = sid.strip()
            if sid in seen:
                self.finding("error", "duplicate_site_id", site_id=sid)
            seen.add(sid)
            if raw.get("revision_of") is not None and raw["revision_of"] != sid:
                self.finding("error", "invalid_revision", site_id=sid)
            context = dict(site_id=sid, scope=scope, manifest=str(path))
            self.sites.append(dict(context, revision_of=raw.get("revision_of")))
            products = raw.get("products")
            if not isinstance(products, list) or not products:
                self.finding("error", "missing_products", site_id=sid)
                continue
            if raw.get("expected_products") is not None and raw["expected_products"] != len(products):
                self.finding("error", "product_count_mismatch", site_id=sid, actual=len(products), expected=raw["expected_products"])
            registered = defaultdict(set)
            handles = set()
            for index, product in enumerate(products):
                if not isinstance(product, dict):
                    self.finding("error", "invalid_product", site_id=sid, index=index)
                    continue
                handle = product.get("handle")
                if isinstance(handle, str) and handle.strip():
                    if handle in handles:
                        self.finding("error", "duplicate_handle", site_id=sid, handle=handle)
                    handles.add(handle)
                else:
                    self.finding("error", "missing_product_handle", site_id=sid, index=index)
                source = product_url(product.get("source_url"))
                keys = set()
                for name in ("product_key", "family_key"):
                    key = product.get(name)
                    if isinstance(key, str) and key.strip():
                        keys.add(key.strip())
                    else:
                        self.finding("review", "missing_identity", site_id=sid, index=index, field=name)
                if source:
                    keys.add("url:" + source)
                    source_id = product.get("source_product_id")
                    if source_id is not None and str(source_id).strip():
                        keys.add("source:" + urlsplit(source).hostname + ":" + str(source_id))
                else:
                    self.finding("error", "invalid_source_url", site_id=sid, index=index)
                aliases = product.get("alias_keys", [])
                if not isinstance(aliases, list) or any(not isinstance(k, str) or not k.strip() for k in aliases):
                    self.finding("error", "invalid_alias_keys", site_id=sid, index=index)
                else:
                    keys.update(k.strip() for k in aliases)
                review = product.get("identity_review")
                if not isinstance(review, str) or not review.strip():
                    self.finding("review", "identity_not_reviewed", site_id=sid, index=index)
                self.products.append(dict(context, index=index, handle=handle, keys=keys))
                images = product.get("images")
                if not isinstance(images, list) or not images:
                    self.finding("error", "missing_product_images", site_id=sid, index=index)
                else:
                    for image_index, image in enumerate(images):
                        key = self.add_image(image, context, path.parent, "product", index, image_index)
                        if key:
                            registered[handle].add(key)
            images = raw.get("images", [])
            if not isinstance(images, list):
                self.finding("error", "invalid_site_images", site_id=sid)
            else:
                for image in images:
                    self.add_image(image, context, path.parent, "marketing", None)
            if scope == "plan":
                paths = raw.get("csv_paths", [])
                if not isinstance(paths, list) or any(not isinstance(p, str) or not p for p in paths):
                    self.finding("error", "invalid_csv_paths", site_id=sid)
                elif not paths:
                    self.finding("review", "final_csv_not_checked", site_id=sid)
                else:
                    self.check_csv(paths, path.parent, sid, handles, registered)

    def add_image(self, raw, context, base, role, product_index, image_index=0):
        raw = {"source_url": raw} if isinstance(raw, str) else raw
        if not isinstance(raw, dict):
            self.finding("error", "invalid_image", site_id=context["site_id"])
            return None
        source = public_url(raw.get("source_url"))
        keys = set()
        if source:
            keys.add("url:" + source)
        else:
            self.finding("error", "invalid_image_url", site_id=context["site_id"])
        for name in ("source_id", "parent_source_id"):
            value = raw.get(name)
            if isinstance(value, str) and value.strip():
                keys.add("source_id:" + value.strip())
        local = raw.get("path")
        fingerprint = None
        if isinstance(local, str) and local:
            local = (base / local).resolve()
            try:
                if local not in self.fingerprints:
                    sha = sha256_file(local)
                    pix, perceptual = (None, None)
                    if Image is not None:
                        pix, perceptual, _, _ = pixel_fingerprints(local)
                    self.fingerprints[local] = (sha, pix, perceptual)
                sha, pix, fingerprint = self.fingerprints[local]
                keys.add("sha256:" + sha)
                if pix:
                    keys.add("pixels:" + pix)
                else:
                    self.finding("review", "pixel_check_unavailable", site_id=context["site_id"])
            except (OSError, ValueError):
                self.finding("review", "image_file_unreadable", site_id=context["site_id"], path=str(local))
        else:
            self.finding("review", "image_content_not_checked", site_id=context["site_id"], product_index=product_index)
        self.images.append(dict(context, role=role, product_index=product_index, is_primary=(role == "product" and image_index == 0), keys=keys, dhash=fingerprint))
        return source

    def check_csv(self, paths, base, sid, handles, registered):
        found = set()
        for rel in paths:
            try:
                with (base / rel).open(encoding="utf-8-sig", newline="") as stream:
                    reader = csv.DictReader(stream)
                    fields = reader.fieldnames or []
                    handle_key = next((k for k in ("URL handle", "Handle") if k in fields), None)
                    image_keys = [k for k in ("Product image URL", "Variant image URL", "Image Src", "Variant Image") if k in fields]
                    if not handle_key or not image_keys:
                        raise ValueError("missing columns")
                    file_handles = set()
                    for row in reader:
                        handle = row.get(handle_key, "").strip()
                        if handle:
                            file_handles.add(handle)
                        for key in image_keys:
                            value = row.get(key, "").strip()
                            if value and public_url(value) not in registered.get(handle, set()):
                                self.finding("error", "unregistered_csv_image", site_id=sid, csv=str(rel), handle=handle)
                    duplicates = found & file_handles
                    if duplicates:
                        self.finding("error", "csv_product_in_multiple_parts", site_id=sid, handles=sorted(duplicates))
                    found.update(file_handles)
            except (OSError, ValueError, TypeError, csv.Error):
                self.finding("error", "csv_unreadable", site_id=sid, csv=str(rel))
        if found != handles:
            self.finding("error", "csv_manifest_mismatch", site_id=sid, csv_only=sorted(found - handles), manifest_only=sorted(handles - found))

    def duplicates(self, records, kind):
        # Connected components catch aliases A=B, B=C without assuming distinct IDs mean distinct styles.
        parent = list(range(len(records)))
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        key_owner = {}
        for index, item in enumerate(records):
            for key in item["keys"]:
                if key in key_owner:
                    parent[find(index)] = find(key_owner[key])
                else:
                    key_owner[key] = index
        groups = defaultdict(list)
        for index, record in enumerate(records):
            groups[find(index)].append(record)
        for group in groups.values():
            sites = sorted({record["site_id"] for record in group})
            if len(sites) > 1 and any(record["scope"] == "plan" for record in group):
                self.finding("error", "cross_site_" + kind, site_ids=sites, records=len(group))
            if kind == "product_family":
                current = defaultdict(list)
                for record in group:
                    if record["scope"] == "plan":
                        current[record["site_id"]].append(record)
                for site_id, entries in current.items():
                    if len(entries) > 1:
                        self.finding("error", "same_site_duplicate_product_family", site_id=site_id, handles=[entry["handle"] for entry in entries], records=len(entries))
            elif kind == "photo":
                current = defaultdict(set)
                for record in group:
                    if record["scope"] == "plan" and record.get("is_primary"):
                        current[record["site_id"]].add(record["product_index"])
                for site_id, product_indices in current.items():
                    if len(product_indices) > 1:
                        self.finding("review", "same_site_primary_photo_shared", site_id=site_id, product_indices=sorted(product_indices), message="Check actual style identity; distinct handles/family labels alone do not prove distinct goods.")

    def finish(self):
        known = defaultdict(list)
        for site in self.sites:
            known[site["site_id"]].append(site)
        for sid, entries in known.items():
            plans = [s for s in entries if s["scope"] == "plan"]
            if len(plans) > 1 or (plans and len(entries) > 1 and plans[0].get("revision_of") != sid):
                self.finding("error", "site_id_collision", site_id=sid)
        self.duplicates(self.products, "product_family")
        self.duplicates(self.images, "photo")
        # Seven bands: at distance <=6, at least one band must match. Limit findings,
        # report overflow explicitly; this is a candidate search, never an exact proof.
        buckets = defaultdict(list)
        review_count = 0
        fingerprint_groups = defaultdict(list)
        for index, item in enumerate(self.images):
            fingerprint = item["dhash"]
            if fingerprint is None:
                continue
            fingerprint_groups[fingerprint].append(index)
        for fingerprint, indices in fingerprint_groups.items():
            sites = {self.images[i]["site_id"] for i in indices}
            if len(sites) > 1 and any(self.images[i]["scope"] == "plan" for i in indices):
                # Exact-image groups have already been reported; distinct pixels
                # with the same perceptual hash still need human inspection.
                signatures = {tuple(sorted(self.images[i]["keys"])) for i in indices}
                if len(signatures) > 1:
                    self.finding("review", "same_perceptual_hash", site_ids=sorted(sites), image_indices=indices[:50], total_images=len(indices))
        for fingerprint, indices in fingerprint_groups.items():
            candidates = set()
            for band in range(7):
                start, end = band * 64 // 7, (band + 1) * 64 // 7
                key = (band, (fingerprint >> start) & ((1 << (end - start)) - 1))
                candidates.update(buckets[key])
                buckets[key].append(fingerprint)
            sites = {self.images[i]["site_id"] for i in indices}
            has_plan = any(self.images[i]["scope"] == "plan" for i in indices)
            for other_hash in candidates:
                other_indices = fingerprint_groups[other_hash]
                other_sites = {self.images[i]["site_id"] for i in other_indices}
                other_plan = any(self.images[i]["scope"] == "plan" for i in other_indices)
                if (sites == other_sites and len(sites) == 1) or not (has_plan or other_plan):
                    continue
                distance = bin(fingerprint ^ other_hash).count("1")
                if distance <= 6:
                    self.finding("review", "near_photo", site_ids=sorted(sites | other_sites), image_indices=[other_indices[0], indices[0]], distance=distance)
                    review_count += 1
                    if review_count >= 500:
                        break
            if review_count >= 500:
                self.finding("review", "near_photo_scan_capped", message="500 candidates found; remaining perceptual comparisons not run. Resolve/deduplicate and rerun.")
                break
        errors = sum(x["severity"] == "error" for x in self.findings)
        reviews = sum(x["severity"] == "review" for x in self.findings)
        return dict(sites=len(self.sites), product_records=len(self.products), image_records=len(self.images), local_files_checked=len(self.fingerprints), errors=errors, review=reviews, findings=self.findings, exit_code=1 if errors else 2 if reviews else 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--history", action="append", default=[], type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    audit = Audit()
    audit.read(args.plan)
    for path in args.history:
        audit.read(path, "history")
    report = audit.finish()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "findings"}))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
