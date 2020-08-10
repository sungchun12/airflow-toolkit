# terragrunt_infrastructure_live

This directory is intended to keep your terraform code DRY using terragrunt. If you follow the traditional terraform-only approach, you will duplicate your code multiple times.

There is a simple dev example, and you can mirror the folder structure for other environments like QA and PROD.

## Deployment Instructions

```bash
cd non-prod/us-central1/

terragrunt plan-all
```

## Notes

terraform keeps overriding state as modules run in parallel to compete for state

## Resources

[Keep your Terraform code DRY](https://terragrunt.gruntwork.io/docs/features/keep-your-terraform-code-dry/)
[Relative Paths](https://community.gruntwork.io/t/relative-paths-in-terragrunt-modules/144/6)
[Handling Dependencies](https://community.gruntwork.io/t/handling-dependencies/315/2)
[Terraform force unlock](https://www.terraform.io/docs/commands/force-unlock.html)
