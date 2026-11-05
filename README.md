# Xiaoqi official capabilities

Public source and versioned release packages maintained by the Xiaoqi team.
“Official” identifies the maintainer; Xiaoqi still asks users to install a
capability and separately checks any host permissions it requests.

## Packages

| Package | Format | Scope |
| --- | --- | --- |
| `study-notes-studio` | Skill | Study-note image planning and review handbook |
| `book-to-skill` | Skill | Book extraction and skill-package checks |
| `original-reading-annotations` | Plugin | OCR-backed annotations while preserving the source image |
| `learning-notes-manager` | Plugin | Rules for adding study knowledge to native Xiaoqi notes |

Each directory is a separately versioned package. A release contains only that
package. Sources, attribution, and licenses remain with the package. Host APIs,
private user material, approval decisions, note storage, and task state belong
to Xiaoqi.

The `capabilities` field is a version-specific request for a Xiaoqi host feature.
Only a package installed from this trusted catalog can use those claims, and
Xiaoqi still applies its own authorization checks. The original annotation
package requests `image.annotate_original`; the notes manager requests
`learning_notes.append`.

## Install and update

Xiaoqi reads [`catalog.json`](catalog.json) for the latest stable version and
its immutable GitHub Release asset, SHA-256, source commit, and host requirements.
The user chooses whether to install an update. A running task stays on its
recorded package version; new tasks use the installed current version.

## Release a package

Review and merge the package change on `main`, tag that source commit as
`<package>-v<version>`, then run the **Publish capability** workflow with that
package, version, and source commit. The workflow validates and packages only
the named capability, publishes its immutable asset, and updates the catalog.
