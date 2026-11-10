---
name: lingmind-operator-jenkins-build
description: Build LingMind repositories with Jenkins, verify the Git revision and resulting image, diagnose slow or failing builds, and validate scoped changes to build pipelines or dependency and image sources.
---

# LingMind Jenkins build and maintenance

This skill covers source control and CI. For any target environment operation, read the
[Operator Agent binding](../../references/agent-binding.md). Route an explicitly requested deployment through the
[service deployment skill](../lingmind-operator-service-deploy/SKILL.md) after verifying the build.

## Build the intended revision

1. Resolve the repository, configured Git remote, branch or commit, Jenkins job, and component parameters. Use the repository's
   current CI configuration and the job's declared parameters. Refresh remote refs before resolving the requested commit.
   Preserve uncommitted work and use an isolated branch or worktree for changes. If the job accepts a branch but the requested
   commit is pinned, use a ref that resolves to that commit and verify the actual checkout.
2. Use the host's authorized Jenkins connection or the workspace's configured CI CLI if it is provisioned. On a cloud host
   without Jenkins access, report the missing connection. Keep Jenkins and Git credentials in their configured credential
   stores. In LingMind workspaces that provide the Matrix `scripts/lm_devops.py` helper, use its Jenkins status, queue and
   build commands. Check the installed CLI's help for its supported parameters. Respect access denials and keep tokens and
   raw secrets out of logs and reports.
3. For an authorized build, check for an existing queued or running build with the same revision and relevant parameters.
   Track the queue item to its assigned build number. If a trigger times out or its response is ambiguous, reconcile against
   the queue and recent builds before retrying.
4. Wait for a terminal result when the request includes validation. Verify the source SHA Jenkins actually checked out and,
   for an image build, confirm the pushed image tag or digest. Report the build link, result, source SHA and image identity.
   Treat a different SHA or an unverified push as incomplete validation.

## Diagnose and improve builds

- Separate queue wait from checkout, dependency installation, tests, compilation, image build and image push. Compare stage
  timings with recent runs for the same job, and note differences in source, runner, parameters or cache state. Use build logs
  and runner-side evidence to locate the slow step. Browser latency measures access to Jenkins and cannot establish the
  speed of downloads from its build container.
- Apply the smallest evidence-backed fix when the user or repository policy authorizes build maintenance. Prefer stable
  dependency caches, explicit stage timing, and eliminating redundant work while preserving quality checks and artifact
  behavior. Keep the fix in a reviewable branch and verify it on Jenkins using comparable inputs. Use a dedicated
  validation image tag when the job supports one. Report before and after timings, cache conditions, and the change or PR
  link.
- Before changing a package registry, base-image registry, or mirror, compare approved candidates from the same Jenkins
  runner and container with the same dependency inputs. Measure cold and warm cache behavior and compare failures as well
  as elapsed time. Check the effective download endpoints, including URLs embedded in lockfiles. If evidence supports a
  change, update the relevant repository configuration and affected lockfile entries together, verify versions and
  integrity, and preserve the existing image platform and trust policy. Treat a Git remote migration as a separate
  explicitly scoped change.
- Build requests authorize the requested CI work. Changes to a shared Jenkins job, runner networking or VPN, production
  sources, protected branches, or deployed services have separate scope. When evidence or permissions are missing,
  report the missing check and keep any proposed change in review.
