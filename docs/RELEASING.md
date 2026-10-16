# Releasing

Releases are published by GitHub Actions (`.github/workflows/release.yml`) **only when a version tag
is pushed**. Nothing is published from a developer's computer.

## Steps

1. Make sure `main` is green in CI and `CHANGELOG.md` lists the changes under `## [Unreleased]`.
2. Set the version everywhere (Python, Django, npm, CHANGELOG):

   ```bash
   python scripts/release/set_version.py 1.2.3
   git commit -am "Release 1.2.3"
   git push
   ```

3. Create and push the tag (or create a release with this tag on GitHub):

   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```

The workflow then:

1. checks that every version matches the tag;
2. re-runs every test (data, Python, Django, JavaScript, API, docs, Go);
3. publishes `naija-data` and `django-naija` to PyPI and `naija-data` to npm (trusted publishing, no tokens);
4. tags the Go module as `go/v1.2.3`;
5. creates the GitHub release with the CHANGELOG notes (marked pre-release for `0.x` and `-rc` versions);
6. installs each package from PyPI, npm and the Go proxy to prove the release works.

npm trusted publishing is configured on npmjs.com (package `naija-data` → Settings → Trusted
Publisher: GitHub Actions, owner `asgatcreation`, repository `naija-data`, workflow `release.yml`,
environment `npm`). A new configuration must be used for a publish within 2 days, so set it up just
before tagging a release that publishes a new npm version.

PyPI and npm never allow the same version number to be published twice, even after deleting it.
If something goes wrong after publishing, fix it and release the next patch version.

## Versions

[Semantic versioning](https://semver.org/): MAJOR for breaking API changes or changed record
identifiers, MINOR for new functions, datasets or records, PATCH for fixes and data corrections.
Release candidates use `1.2.3-rc.1` (Python `1.2.3rc1`, npm dist-tag `next`).
