# Publishing MedSystem1

## First upload to PyPI

The GitHub v0.1.0 release is an alpha prerelease. The package version inside
that immutable source tag is `0.1.0`. Main is a separate development line;
do not upload main under the v0.1.0 version or move the existing tag.

1. Register a personal account at <https://pypi.org/account/register/>.
   Verify the email and enable PyPI's required two-factor authentication.
   Keep passwords, recovery codes, and one-time codes out of GitHub and chat.
2. In account settings, open **Publishing**:
   <https://pypi.org/manage/account/publishing/>.
3. Add a **pending GitHub Actions publisher** for a project that does not yet
   exist. Use these exact values:

   | Field | Value |
   | --- | --- |
   | PyPI project name | `medsystem1` |
   | Owner | `qiqilong01-wq` |
   | Repository name | `MedSystem1` |
   | Workflow filename | `publish-pypi.yml` |
   | Environment name | `pypi` |

   The workflow filename is the basename, not `.github/workflows/...`.
   The environment must match the existing workflow's `environment: pypi`.
   Adding this publisher authorizes this repository/workflow/environment to
   upload this package. Review those bindings before submitting.
4. Open the original v0.1.0 publication run:
   <https://github.com/qiqilong01-wq/MedSystem1/actions/runs/37494347235>.
   Use **Re-run failed jobs** after the publisher has been registered. A rerun
   uses the original tag's commit and workflow; main's later edits do not change it.
5. Verify all of the following before reporting publication complete:
   - The GitHub publishing job succeeds.
   - <https://pypi.org/project/medsystem1/0.1.0/> exists and lists wheel and sdist.
   - In a fresh environment, `python -m pip install medsystem1==0.1.0` works.
   - An import reports `medsystem1.__version__ == "0.1.0"` and the README
     quick start returns LOCAL for bounded extraction and HUMAN_REVIEW for treatment changes.

Trusted Publishing uses OIDC; this workflow needs no persistent PyPI API token.
A pending publisher does not reserve the package name. Check ownership if the
name becomes unavailable; do not upload to an unrelated owner's project.

## Failure handling

`invalid-publisher` means no publisher matched the OIDC identity. Compare the
five fields above with the repository and checked-in workflow. Do not disable
OIDC checks or add credentials to the source to work around a mismatch.

If a rerun reports an existing distribution, inspect PyPI's actual files and
version before retrying. PyPI versions cannot be overwritten; a corrected
distribution needs a new version. Do not delete the original release/tag just
to trigger publishing again.

## Future releases

Main is `0.1.1.dev0` after v0.1.0. The next patch is unreleased until explicitly
tagged. Before releasing, update `pyproject.toml` and `medsystem1.__version__`
together, update CHANGELOG, and run:

```bash
python -m pip install -e ".[dev]" build twine
ruff check .
pytest -q
python -m build
python -m twine check --strict dist/*
```

Use a clean distribution directory and a tag of `v<package-version>`.
Publish a GitHub release from that tag. The publishing workflow validates
lint, tests, tag/version agreement, and metadata before the OIDC upload.

Official reference:
<https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/>.
