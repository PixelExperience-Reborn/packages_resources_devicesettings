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

## Android17 integration decisions

- The staged manifest currently contains neither the old PE resource project nor a reviewed mondrian product integration; keep this as an audit-only P1 candidate.
- `SettingsLibDefaults` and `androidx.preference_preference` must be verified against the **actual** Android17 Soong graph. A raw module rename, static link or copied legacy `Android.bp` is not a verified A17 port.
- Before a future `XiaomiParts` integration, choose one explicit path: (a) bring a reviewed, compatible version of the LineageOS resource library with correctly defined independent Soong module and namespaced symbols, or (b) port the actual *required* resources to a PE-specific module and update `XiaomiParts` itself in a separate mondrian-only device branch. Both require per-symbol review. Neither is implemented by this audit.
- Avoid defining user controls without their corresponding hardware HAL. The existing device Haptic Engine, touch configuration, Pocket Mode and display settings are independent implementations: labels for features that are not supported must not be shown.
- Preserve current EN/RU/UK locales, avoid symbol reuse and translation-format mismatches. Check `aapt2`, runtime overlays, large fonts, RTL and UI tests before any product enablement.

## Acceptance gates

- [x] Identify historical PE module, revision, no-code manifest and strings-only behavior.
- [x] Compare with actual `XiaomiParts` resource dependency and upstream LineageOS library identity.
- [x] Check old patch history and removed Haptic Level labels.
- [x] Create a host-only XML/resource-inventory check in this isolated branch.
- [ ] Resolve all `XiaomiParts` referenced library resources (symbols, layouts and style attributes); compare RU/EN/UK resource keys and namespace/accessibility behavior.
- [ ] Verify Android17 Soong libraries and `aapt2` for the **chosen** resource implementation; no untested `SettingsLibDefaults` migration.
- [ ] Select a consistent product/vendor ownership model that does not import full LineageOS build base into a clean PE platform.
- [ ] Compile `XiaomiParts` under AOSP17 using its complete Soong/Compose graph, privileges/SELinux and tested device-specific feature gates.
- [ ] Boot and test all enabled controls on mondrian, including post-reboot behavior and locales.

**Decision:** not a missing AOSP17 core source, not a HAL and not a production-ready PE replacement for the device's `org.lineageos.settings.resources`. Do not include in a staged manifest until a consumer-level build proves the resource mapping.
