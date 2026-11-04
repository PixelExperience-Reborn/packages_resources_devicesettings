#!/usr/bin/env python3
"""Host-only XML and module provenance check of the archived PE resources."""
from collections import Counter
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = "{http://schemas.android.com/apk/res/android}"


def require(ok, description):
    if not ok:
        raise AssertionError(description)
    print("PASS:", description)


def main():
    bp = (ROOT / "Android.bp").read_text(encoding="utf-8")
    require(re.search(r'android_library\s*\{\s*name:\s*"org.pixelexperience.settings.resources"', bp) is not None,
            "historical PE resources android_library identity")
    require('"SettingsLibDefaults"' in bp and 'sdk_version: "current"' in bp,
            "historical SettingsLib defaults and SDK, NOT proven valid on AOSP17")
    require('"androidx.core_core"' in bp and '"androidx.preference_preference"' in bp,
            "legacy resources Soong dependencies recorded")
    require('"org.lineageos.settings.resources"' not in bp,
            "PE module does not satisfy XiaomiParts LineageOS resource name")
    manifest = ET.parse(ROOT / "AndroidManifest.xml").getroot()
    app = manifest.find("application")
    require(manifest.get("package") == "org.pixelexperience.settings.resources"
            and app is not None and app.get(NS + "hasCode") == "false",
            "resources package declares no application code")
    require(not list(ROOT.rglob("*.java")) and not list(ROOT.rglob("*.kt")),
            "historical source contains no Java or Kotlin feature implementation")

    xmls = sorted((ROOT / "res").rglob("*.xml"))
    require(len(xmls) >= 150, "resource XML inventory is present")
    errors = []
    for path in xmls:
        try:
            ET.parse(path)
        except ET.ParseError as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    require(not errors, "all resource XML files parse: " + "; ".join(errors[:8]))
    # AAPT2 resource uniqueness is per qualifier directory and resource type.
    # Inventory *all* locales rather than only the three languages initially
    # examined. Do not silently convert resource collisions into CI success.
    collisions = []
    checked = 0
    for directory in sorted((ROOT / "res").iterdir()):
        if not directory.is_dir() or not directory.name.startswith("values"):
            continue
        definitions = {}
        for path in sorted(directory.glob("*.xml")):
            root = ET.parse(path).getroot()
            for item in root:
                name = item.get("name")
                if not name:
                    continue
                kind = item.get("type") if item.tag == "item" else item.tag
                kind = "array" if kind in ("array", "string-array") else kind
                key = (kind, name)
                if key in definitions:
                    collisions.append(f"{directory.name}: {kind}/{name} "
                                      f"in {definitions[key]} AND {path.name}")
                else:
                    definitions[key] = path.name
        checked += 1
        if directory.name in ("values", "values-ru", "values-uk"):
            for filename in ("strings.xml", "custom_strings.xml"):
                require((directory / filename).is_file(),
                        f"{directory.name}/{filename} exists")
            print(f"LOCALE INVENTORY: {directory.name}: {len(definitions)} resources")
    require(checked >= 130, f"all translation qualifiers checked: {checked}")
    if collisions:
        for issue in collisions[:40]:
            print("BLOCKER duplicate Android resource:", issue, file=sys.stderr)
        print(f"BLOCKER total resource collisions: {len(collisions)}", file=sys.stderr)
    require(not collisions, "AAPT2 resource identifier uniqueness across locale XMLs")
    main_strings = (ROOT / "res/values/custom_strings.xml").read_text()
    require('name="dirac_title"' in main_strings and 'name="powershare_enable_title"' in main_strings,
            "archived Dirac and powershare display labels (NOT HAL features)")
    require('name="haptic_level_title"' not in main_strings,
            "removed historical Haptic Level string not inadvertently restored")
    require('name="device_settings_app_name"' in (ROOT / "res/values/strings.xml").read_text(),
            "device settings title exists")
    print("PASS: historic XML + Soong-name inventory only. No AOSP17 aapt2/Soong/mondrian build.")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, ET.ParseError) as exc:
        print("FAIL:", exc, file=sys.stderr)
        sys.exit(1)
