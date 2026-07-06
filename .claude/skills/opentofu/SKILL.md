---
name: opentofu
description: OpenTofu/Terraform conventions — repo structure, environment/module split, versioning, ownership. Use when writing, structuring, or reviewing OpenTofu/Terraform code, adding resources, or creating environments.
---

# OpenTofu conventions

Follows the Google Cloud Terraform best-practices guides and HashiCorp style guide; deviations noted inline.

## Structure

```
infra/
  scripts/                 # imperative bootstrap — chicken-and-egg only
  opentofu/
    environments/<env>/    # one root per env = one isolated state (ideally one cloud project/account)
      backend.tf           # remote state backend, fully declared
      providers.tf         # required_version + ~> pinned providers + provider config
      main.tf              # module call(s), env values inlined
      variables.tf         # only for values CI injects at run time
      outputs.tf           # re-exports module outputs
      .terraform.lock.hcl  # committed
    modules/<service>/     # a deployable stack as one composable unit
      versions.tf          # required_providers: sources + minimum versions (>=) only
      variables.tf         # no-default (env-differentiating) vars first, defaulted second
      locals.tf            # module-wide labels + derived values
      <concern>.tf         # one file per concern: network.tf, iam.tf, database.tf, apis.tf, ...
      outputs.tf
      README.md            # what it provisions + contracts
```

- Directories per environment, never CLI workspaces. Keep states small (well under 100 resources); split roots before exceeding.
- One file per concern in modules — no monolithic `main.tf`. Any resource is findable from the filename.
- Split a service module into concern modules (network, db, service, ...) composed in the env root — outputs wired into inputs — once it holds more than one deployable service. Until then, one module split by concern files is fine.

## Environment roots

- Roots are boring: backend, providers, module call(s), outputs. No resources, no logic.
- Inline values in module calls — no tfvars (deliberate deviation: tfvars only pays off when one root runs with different value sets, which one-root-per-env rules out). Root `variable` blocks only for run-time CI injection (`TF_VAR_*` / `-var`).
- Inline only public config (project ids, regions, URLs, origins). Secrets never in roots, tfvars, or state — use a secret manager.
- New env = copy a root, fill backend + project/region, bootstrap its state. Prod differs via module arguments (deletion protection, tiers, scoped CI roles), not different code.

## Versioning

- Root: pins `required_version` + providers with `~>`; owns the committed lock file.
- Module: `required_providers` with sources + `>=` minimums only. Modules never configure providers or backends.

## Ownership

- **Two planes.** Bootstrap scripts create only what IaC can't self-create (state backend, CI↔cloud OIDC trust). Everything declarative lives in modules. Never grow the scripts.
- **IaC owns shape, CI owns releases.** CI-built services: placeholder image + `ignore_changes` on the image attribute; the pipeline updates only the image. A plan after a release must be clean — extend `ignore_changes` if CI-written attributes churn it.
- **APIs enabled declaratively** (`google_project_service`, `for_each`, `disable_on_destroy = false`) with `depends_on` from consumers. Deferred APIs stay commented with their enabling trigger.
- **Keyless everywhere:** CI via OIDC/WIF, workload→DB via IAM auth. Needing a stored secret triggers secret-manager adoption, never a workaround.

## Resources

- Every variable: `type` + `description` stating the contract (e.g. "creation only; live image is CI-owned").
- Every label-supporting resource gets `local.labels` (at minimum project + `managed = "opentofu"`).
- Module outputs carry descriptions; roots re-export bare.
- Eventual-consistency races get an explicit `time_sleep` with a comment naming the race.
- Deferred decisions: `TODO` at the site with the trigger condition ("private IP when compliance requires it").
- Destroy guards (`deletion_protection`, `prevent_destroy`) are module variables — prod enables what dev disables.

## Workflow

1. Change modules; touch roots only for env values.
2. Plan against dev before pushing — only the intended change may appear.
3. Apply via CI on main; local applies are the exception.
4. Structure or contract changes update the READMEs — docs lead, code follows.
