# Isolated resource collision fix — Android 17 PE-Reborn investigation

Date: 2026-11-04.

## Baseline and scope

The historical PixelExperience-Reborn `packages_resources_devicesettings` branch `seventeen` is **unchanged**. This branch descends from the independent audit branch `audit/a17-mondrian-devicesettings-20261104` and demonstrates one minimal resource correction; it is **not** an Android17 product integration or device settings replacement.

The audit CI first reported duplicate `string/button_swap_summary` defined in **two files with the same resource qualifier**: `res/values*/custom_strings.xml` and `res/values*/strings.xml`. The string texts were sometimes different, so this is not a harmless copy of the same declaration. The independent baseline audit intentionally reports the error as a blocking finding: https://github.com/PixelExperience-Reborn/packages_resources_devicesettings/actions/runs/41750686961

## Fix applied

- Removed **only** the duplicate `<string name="button_swap_summary">...</string>` entry from `custom_strings.xml` in 34 affected resource qualifiers.
- Kept the canonical `strings.xml` entry and all other localized resources untouched, including English, Russian and Ukrainian definitions in that file.
- Split the file edits across three fast-forward commits for auditability:
  - `65cb4798d3003f5bf413df2155d10885907fcb0a` — 12 qualifiers.
  - `76fd18facbbf0cd32af52a5706a5814167c509a4` — 12 qualifiers.
  - `8547bf2293d23c24fb6723c64bbd28392955622c` — 10 qualifiers.
- Expanded host CI source inventory verifies XML parsing and duplicate identifiers across **all 140 values-qualifier directories**, not just RU/UK; this source test still does not run AAPT2.
- The conflicting `button_swap_summary` definitions already existed historically. This fix is **not** evidence that the old device-settings resource library compiles with Android17.

## Architecture decision

New **PixelExperience-Reborn** device trees for mondrian and sm8450-common must be created as native AOSP17/PE product implementations. Existing `LF52406` LineageOS-derived device trees are a **hardware reference** only; they must not be inherited unchanged or used to choose the product architecture. In particular, the current `XiaomiParts` module's `org.lineageos.settings.resources` dependency is not resolved by this resource fix. Do not import or alias the LineageOS resource library automatically.

Before any manifest activation:
1. Define native PE Reborn `device/xiaomi/mondrian` and `device/xiaomi/sm8450-common` product ownership and baseline vendor/kernel interfaces.
2. Identify which resources are required for the new, independently designed hardware settings components.
3. Verify the exact Android17 Soong `SettingsLibDefaults` and AndroidX resource graph; build with `aapt2` and `m` in an AOSP17 tree.
4. Check XML resource names, locale coverage, themes, overlays, hardware feature gates and no colliding dependency module names.
5. Test on POCO F5 Pro / Redmi K60 and only then consider a reviewed optional staging profile.

**Do not merge the historical library into the active Android17 manifest.** This branch fixes proven resource-input problems only.
