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
    for locale in ("values", "values-ru", "values-uk"):
        directory = ROOT / "res" / locale
        keys = []
        for filename in ("strings.xml", "custom_strings.xml"):
            path = directory / filename
            require(path.is_file(), f"{locale}/{filename} exists")
            root = ET.parse(path).getroot()
            keys.extend(item.get("name") for item in root if item.get("name"))
        require(len(keys) == len(set(keys)), f"{locale} resource entries have distinct names")
        print(f"LOCALE INVENTORY: {locale}: {len(keys)} named resource entries")
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
