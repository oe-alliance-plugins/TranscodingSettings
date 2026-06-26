

# <p align="center">TranscodingSettings Plugin for Enigma2 (E²) ![GitHub repo size](https://img.shields.io/github/repo-size/oe-alliance-plugins/TranscodingSettings.svg)</p>

**TranscodingSettings**

## Github status
[![Build](https://github.com/oe-alliance-plugins/TranscodingSettings/actions/workflows/buildbot.yml/badge.svg)](https://github.com/oe-alliance-plugins/TranscodingSettings/actions/workflows/buildbot.yml)
[![Lint Status](https://github.com/oe-alliance-plugins/TranscodingSettings/actions/workflows/pylint.yml/badge.svg)](https://github.com/oe-alliance-plugins/TranscodingSettings/actions/workflows/pylint.yml)
[![Ruff Status](https://github.com/oe-alliance-plugins/TranscodingSettings/actions/workflows/ruff.yml/badge.svg)](https://github.com/oe-alliance-plugins/TranscodingSettings/actions/workflows/ruff.yml)
[![Build Status](https://github.com/oe-alliance-plugins/TranscodingSettings/actions/workflows/compile.yml/badge.svg)](https://github.com/oe-alliance-plugins/TranscodingSettings/actions/workflows/compile.yml)
[![AUTOTAG](https://github.com/oe-alliance-plugins/TranscodingSettings/actions/workflows/autotag.yml/badge.svg)](https://github.com/oe-alliance-plugins/TranscodingSettings/actions/workflows/autotag.yml)


[![Plugin Version](https://img.shields.io/github/v/tag/oe-alliance-plugins/TranscodingSettings?label=Latest%20Version&color=darkviolet)](https://github.com/oe-alliance-plugins/TranscodingSettings/tags)
[![Latest Release](https://img.shields.io/github/release-date/oe-alliance-plugins/TranscodingSettings?label=From&color=darkviolet)](https://github.com/oe-alliance-plugins/TranscodingSettings/releases/latest)
[![Github last commit](https://img.shields.io/github/last-commit/oe-alliance-plugins/TranscodingSettings)](https://github.com/oe-alliance-plugins/TranscodingSettings)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/oe-alliance-plugins/TranscodingSettings.svg?label=commits)](https://github.com/oe-alliance-plugins/TranscodingSettings/commits)
[![GitHub Activity](https://img.shields.io/github/commit-activity/m/oe-alliance-plugins/TranscodingSettings.svg?label=commits)](https://github.com/oe-alliance-plugins/TranscodingSettings/commits)

## SonarCloud status
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance-plugins_TranscodingSettings&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=oe-alliance-plugins_TranscodingSettings)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance-plugins_TranscodingSettings&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=oe-alliance-plugins_TranscodingSettings)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance-plugins_TranscodingSettings&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=oe-alliance-plugins_TranscodingSettings)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance-plugins_TranscodingSettings&metric=bugs)](https://sonarcloud.io/summary/new_code?id=oe-alliance-plugins_TranscodingSettings)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance-plugins_TranscodingSettings&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=oe-alliance-plugins_TranscodingSettings)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance-plugins_TranscodingSettings&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=oe-alliance-plugins_TranscodingSettings)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance-plugins_TranscodingSettings&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=oe-alliance-plugins_TranscodingSettings)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance-plugins_TranscodingSettings&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=oe-alliance-plugins_TranscodingSettings)

[![SonarQube Cloud](https://sonarcloud.io/images/project_badges/sonarcloud-light.svg)](https://sonarcloud.io/summary/new_code?id=oe-alliance-plugins_TranscodingSettings)

---


# TranscodingSettings

Unified Enigma2 SystemPlugin for hardware transcoding and the optional
`enigma2-live555` HLS/RTSP service.

## Direct Enigma2 configuration

The plugin defines its configuration once and uses it directly everywhere:

```python
config.plugins.transcodingsettings = ConfigSubsection()
```

The config tree is:

```text
config.plugins.transcodingsettings.enabled
config.plugins.transcodingsettings.port
config.plugins.transcodingsettings.encoder
config.plugins.transcodingsettings.encoder0.*
config.plugins.transcodingsettings.encoder1.*
config.plugins.transcodingsettings.live.*
config.plugins.transcodingsettings.hls.*
config.plugins.transcodingsettings.rtsp.*
```

`encoder0` and `encoder1` are created only for detected physical encoders. They
are ordinary named `ConfigSubsection` objects; no `ConfigSubList` is used.
There is no dynamic top-level section helper and no old-setting migration.
Calling `config.plugins.transcodingsettings.save()` or `.cancel()` recursively
handles the complete tree using Enigma2's normal config implementation.

## BoxInfo capability interface

The following mutable capability values are published when the plugin probes the
receiver:

```text
HasTranscodingSettings
TranscodingSettingsEncoderCount
TranscodingSettingsPort8001
TranscodingSettingsPort8002
TranscodingSettingsLive555
TranscodingSettingsHDMIInput
TranscodingSettingsEncoderSelection
```

They intentionally remain in the plugin. They let OpenWebif decide whether to
use the new Enigma2 path without importing plugin implementation helpers.
Configuration values themselves remain exclusively in
`config.plugins.transcodingsettings`.

## Availability

The plugin returns no Enigma2 descriptors when no usable encoder is detected.
It supports `/proc/stb/encoder/<index>`, `/dev/bcm_enc<index>`,
`/dev/encoder<index>`, and Dreambox `/dev/venc0` plus `/dev/aenc0`.
Only encoder 0 and encoder 1 are exposed.

The selector defaults to **Auto (first free)**. Fixed encoder 0/1 selection is
available for diagnostics and special clients.

## Ports and protocols

- **8001**: Enigma2 stream server; optional HLS/RTSP via `enigma2-live555`.
- **8002**: classic BCM transcoding path; HLS/RTSP are never available.

HLS and RTSP are disabled by default. The daemon is started on demand only when
at least one endpoint is enabled while transcoding uses port 8001, and stopped
again when neither endpoint is needed.

## User interface

The Basic view provides presets. Yellow opens the preset chooser, Blue toggles
Advanced, and Help displays the full `setup.xml` explanation for the selected
setting.




### 📜 License Information [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

This is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation

This plugin is released under GPLv3. See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.html#license-text) for full details.

<img width="120" height="58" alt="GPLv3_Logo svg" src="https://github.com/user-attachments/assets/67d32b0a-2a44-4fa9-a972-202daf28808e" />

---

### 🤝 Contributing & Contact

TranscodingSettings is created by users for users and we welcome every contribution. There are no highly paid developers. There are only users who have seen a problem and done their best to fix it. This means TranscodingSettings will always need the contributions of users like you. How can you get involved?

For questions or feedback, feel free and please open an issue or contribute with a Pull Request!

Pull requests are very welcome for:
- **Coding:** Developers can help by fixing a bug, adding new features, Integration improvements, Feature enhancements
- **Localization:** Translate into your native language.
- **Helping users:** Our support process relies on enthusiastic contributors like you to help others.

Your contribution is very welcome! Follow these steps:

1. 🍴 Fork this repository
2. 🔄 Create a branch for your feature
3. 💻 Make your changes
4. ✅ Commit using conventional messages
5. 📤 Push to your branch
6. 🔍 Open a Pull Request

Enjoy and help us improve it today. :)

### 🚨 Disclaimer

The project author is not responsible for how this software is used by others. It is not intended to be used for accessing or distributing copyrighted materials without authorization.
Users are solely responsible for determining the legality of their actions.

This repository has no control over the streams, links, or the legality of the content provided by the different hosts (including all mirror sites). It is the end user's responsibility to ensure the legal use of these streams, and we strongly recommend verifying that the content complies with all applicable laws, including copyright laws and regulations of your countrys jurisdiction before use.

---

### 🤝 Contributing Details

For detailed contributing guidelines including testing procedures and AI policy, please see [CONTRIBUTING.md](https://github.com/oe-alliance-plugins/.github/blob/main/docs/CONTRIBUTING.md).

---

⭐️ If you find this plugin useful, please give it a star on GitHub!
Thanks! ❤️ 💞 💖 ❤️‍🔥 💗
