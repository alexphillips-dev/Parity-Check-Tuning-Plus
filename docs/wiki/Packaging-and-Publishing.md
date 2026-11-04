# Packaging and publishing

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

## Development policy

Commit completed, reviewed updates and push `dev` with:

```text
git push --no-verify origin dev
```

Use `-u` when establishing upstream tracking. `--no-verify` is the maintainer's requested push behavior and does not replace validation. Do not force-push, rewrite history, promote `main`, or create a public release without separate authorization.

## Before committing

1. Verify repository root, branch, remote, and current remote state.
2. Review affected source, callers, and state.
3. Run appropriate synthetic/catalog/browser checks and `python -B scripts/check_runtime_references.py` when runtime functions change.
4. Rebuild if installed files or the packaged README changed.
5. Verify source parity, dev URLs, checksums, modes/ownership, syntax, and whitespace.
6. Stage only explicit reviewed paths. Run `python -B scripts/check_publish_files.py` against the exact Git index, then review the staged diff for credentials, host data, editor sessions, and fixture output.

## Files that belong in Git

Keep product source and defaults, language catalogs and their authoring inputs, licenses/notices, public documentation/wiki sources, build/validation scripts, dependency manifests/lockfiles, and synthetic test sources with their upstream fixtures. Keep published install archives and matching manifests/checksums: they are distribution inputs and support previously published version URLs.

Agent instructions, editor/assistant state, credentials, private host data, runtime directories, diagnostics, downloaded tools, scan reports, caches, dependencies, and generated browser/test output stay local. Ignore rules cover those categories; `AGENTS.md` remains available locally and is not tracked. The publication guard also rejects unexpected paths and checks exact staged content, so an existing tracked file or force-add cannot silently bypass the ignore policy. Deliberate new public file categories require review of the allowlist.

The guard checks common token/private-key patterns, credential-bearing URLs, workstation paths, personal profile names, nonpublic email addresses, and packaged contents. It also validates the resolved Git author/committer identities, including environment overrides: use a public account alias and GitHub noreply address. Official native parser fixtures retain their public contact/example text only when the exact path and pinned blob match. The guard reports filenames and categories without printing matched values. It complements secret scanners and manual review; it is not proof that arbitrary personal data is absent. Keep raw scan reports under ignored `build/`.

Deleting a tracked file removes it from the current tree. Earlier commits can still contain it. History rewriting and force-pushing require separate authorization; do not represent a normal deletion as historical erasure.

## Issue forms and labels

The reviewed repository-support files are `.github/labels.json` and the six explicitly named `.github/ISSUE_TEMPLATE/*.yml` files. The publication guard allows those exact paths and `requirements-dev.txt`; it does not generally allow GitHub workflows or arbitrary YAML/JSON files. Validate them with `python -B scripts/check_issue_forms.py` after installing development dependencies.

GitHub loads issue forms and the chooser configuration from its default branch, currently `main`. Develop and validate changes on `dev`. Activating a change requires explicit authorization for a commit containing only the reviewed issue-form/label configuration on `main`; do not merge the plugin implementation as part of that operation. Compare the main commit's path list and unchanged README/LICENSE blobs against its remote parent before pushing.

Label definitions are stored in `.github/labels.json`, but GitHub labels are separate repository metadata. Create/update those exact names, descriptions, and colors using GitHub settings or the authenticated CLI before activating forms; a form cannot apply a nonexistent label. Retain existing label names and do not delete labels merely because they are absent from a future catalog without reviewing their use. Form fields do not automatically assign component or priority labels.

Check the rendered issue chooser, all five forms, and live label metadata after publication without submitting test issues. Repository-only support changes do not rebuild or change the installed plugin version.

## Artifacts

The root manifest declares the version and branch (`dev` or `main`). The builder creates matching `.txz`, `.md5`, `.sha256`, and `.plg` snapshots in `archives/`, and updates root hashes. Both update/download URLs must select the declared branch. Malformed/mixed/foreign metadata fails before artifact writes.

Use `python -B scripts/build_package.py --branch dev --dry-run` to preview and `--branch dev` to build development metadata. Prepare main only in an isolated candidate using `--root <candidate> --branch main`; validate with `check_branding.py --root <candidate> --branch main` and `check_docs.py --root <candidate> --branch main`. Main preparation is local and does not authorize merge/push/release. Preserve branch-specific manifests and historical artifacts when integrating branches. See the [complete channel guide](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/STABLE-CHANNEL.md).

Metadata is deterministic: root ownership, LF source, fixed timestamps, controlled executable modes. Root entries, unrelated paths, unsafe types, and unsafe permissions are rejected. Failed validation preserves the previous archive.

## After pushing

Verify the remote dev commit and commit-pinned manifest/archive. Confirm public bytes match local and manifest hashes. Raw branch URLs can be cached, so pinned URLs help diagnose mismatches.

A push is not a stable release, main promotion, CA listing, or live host acceptance.

## Wiki

The wiki is a separate Git repository. Reviewed source pages are mirrored in `docs/wiki/`. Inspect wiki state, copy intended pages, validate links, commit, and push its own default branch using `git push --no-verify`.

Wiki/root-documentation-only changes do not rebuild unchanged installed files. A packaged README change changes package bytes and requires rebuilding.
