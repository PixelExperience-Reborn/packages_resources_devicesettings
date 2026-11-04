# P1 — PixelExperience device settings resources / Android 17 / mondrian audit

Date: 2026-11-04. Scope: **source and resource inventory only, NOT selected in staged AOSP17 manifest**.

## Historical PE source and actual module role

- PixelExperience-Reborn historical `packages_resources_devicesettings`, branch `seventeen`, revision `183b4451592cfe45bfe565d62000ef000a5c5e31` (2023-09-15 translation update). The branch is not an Android17 source.
- The old `Android.bp` declares `android_library { name: "org.pixelexperience.settings.resources" }` with `SettingsLibDefaults`, `androidx.core_core`, `androidx.preference_preference`, `sdk_version: "current"`. It is an **Android resource library**, not a hardware-control app, service or HAL.
- `AndroidManifest.xml` declares `package="org.pixelexperience.settings.resources"` and `android:hasCode="false"`; there is no application entry point for toggling hardware.
- Contains resources and translation directories, including `res/values`, `res/values-ru`, `res/values-uk`, layouts and images. Resource strings mention unrelated devices and features: pop-up camera, OnePlus alert slider, Moto gestures, Dirac, LCD high brightness, powershare, screen-off gestures, Xiaomi tuning. Their presence **does not establish device support**.
- Source lineage: old PE patch `38f9bb4b6692` adds Haptic Level strings, while later `d3bb04f00a65` **removes** them from the default `res/values/custom_strings.xml`; do not resurrect removed settings. Other historical patches include `fc03ecca248a` (Moto strings), `40f86645ef5b` (LCD HBM summary).

## Verified mondrian consumer mismatch — integration blocker

Actual POCO F5 Pro / Redmi K60 (`mondrian`) source:
- `LF52406/mondrian_android_device_xiaomi_sm8450-common` branch `lineage-24.0`, `parts/Android.bp`: privileged/platform-signed `XiaomiParts` explicitly has `static_libs: ["org.lineageos.settings.resources", ...]`, `defaults: ["SettingsLibDefaults", "platform_app_defaults"]`.
- `common.mk` packages `XiaomiParts`; also packages the Xiaomi touch service and health HAL. Do not infer those runtime services from the PE strings.
- Official LineageOS `android_packages_resources_devicesettings` `lineage-24.0` provides `org.lineageos.settings.resources` with its **own package identity**; its `Android.bp` still references `SettingsLibDefaults`.
- The historical PE library is named `org.pixelexperience.settings.resources` and **cannot** satisfy the explicit `org.lineageos.settings.resources` dependency merely by inclusion in the manifest. Replacing names or using both libraries can introduce resource collisions and mixed namespaces. Resolve source ownership and actual used symbols before any device product sync.

## Project architecture boundary: PixelExperience-Reborn device trees

**Do not use the existing LineageOS-based mondrian or sm8450-common trees as the PE-Reborn product baseline.** They are reference implementations for reading board capabilities, HALs, firmware blob names, kernel interfaces and VINTF declarations only. The new PixelExperience-Reborn Android17 product requires independent `device/xiaomi/mondrian` and `device/xiaomi/sm8450-common` sources, its own product inheritance and overlays, and an explicit vendor/kernel ownership decision. Do not carry `vendor/lineage/config`, `lineage_mondrian`, Lineage health/touch services, `org.lineageos.settings.resources`, `XiaomiParts`, or privileged permissions by default. Each must be justified and either redesigned for AOSP17 or excluded. The existence of a feature in the old Lineage-derived trees is not evidence it must be present in PE-Reborn.

In particular, `org.lineageos.settings.resources` is relevant only as a **source of the incompatibility finding**: the old `XiaomiParts` cannot be built unmodified against the archived PE library. It is *not* a recommendation to include LineageOS resources in the new PE product.

### Source-only regression finding

First host CI run 41750359957 failed on a **real duplicate** Android resource `string/button_swap_summary` declared in both `res/values/strings.xml` and `res/values/custom_strings.xml`, with additional instances in `values-ru` and `values-uk`. The two definitions carry different display text. This is an AAPT2 collision risk if this legacy library is built as-is. An expanded check inventories all locale qualifiers and must remain a blocking diagnostic until a consciously designed PE resource module resolves all collisions. No original `seventeen` source or product branch was changed.

## Android17 integration decisions

- The staged manifest currently contains neither the old PE resource project nor a reviewed mondrian product integration; keep this as an audit-only P1 candidate.
- `SettingsLibDefaults` and `androidx.preference_preference` must be verified against the **actual** Android17 Soong graph. A raw module rename, static link or copied legacy `Android.bp` is not a verified A17 port.
- The new PE-Reborn device product must own its hardware settings. Reuse only the *required* resource strings and layouts after designing a PE-specific Soong module and a dedicated mondrian hardware-settings application if appropriate. Do **not** use the old `XiaomiParts` or its Lineage resource dependencies as the default product design. Every migrated symbol needs source ownership and device support verification.
- Avoid defining user controls without their corresponding hardware HAL. The existing device Haptic Engine, touch configuration, Pocket Mode and display settings are independent implementations: labels for features that are not supported must not be shown.
- Preserve current EN/RU/UK locales, avoid symbol reuse and translation-format mismatches. Check `aapt2`, runtime overlays, large fonts, RTL and UI tests before any product enablement.

## Acceptance gates

- [x] Identify historical PE module, revision, no-code manifest and strings-only behavior.
- [x] Compare with actual `XiaomiParts` resource dependency and upstream LineageOS library identity.
- [x] Check old patch history and removed Haptic Level labels.
- [x] Create a host-only XML/resource-inventory check in this isolated branch.
- [ ] Resolve all `XiaomiParts` referenced library resources (symbols, layouts and style attributes); compare RU/EN/UK resource keys and namespace/accessibility behavior.
- [ ] Verify Android17 Soong libraries and `aapt2` for the **chosen** resource implementation; no untested `SettingsLibDefaults` migration.
- [ ] Create a separate PE-Reborn native AOSP17 mondrian + sm8450-common product tree, with explicit vendor/kernel choices, no LineageOS product inheritance, and prove every adopted HAL and resources module independently.
- [ ] Compile `XiaomiParts` under AOSP17 using its complete Soong/Compose graph, privileges/SELinux and tested device-specific feature gates.
- [ ] Boot and test all enabled controls on mondrian, including post-reboot behavior and locales.

**Decision:** not a missing AOSP17 core source, not a HAL and not a production-ready PE replacement for the device's `org.lineageos.settings.resources`. Do not include in a staged manifest until a consumer-level build proves the resource mapping.
