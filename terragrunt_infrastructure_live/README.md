# terragrunt_infrastructure_live

This directory is intended to keep your terraform code DRY using terragrunt. If you follow the traditional terraform-only approach, you will duplicate your code multiple times.

There is a simple dev example, and you can mirror the folder structure for other environments like QA and PROD.

## Deployment Instructions

```bash
# download a service account key
# enable the service account
SERVICE_ACCOUNT_EMAIL="demo-service-account@wam-bam-258119.iam.gserviceaccount.com"
gcloud beta iam service-accounts enable $SERVICE_ACCOUNT_EMAIL

# download a private json key
gcloud iam service-accounts keys create service_account.json \
    --iam-account=$SERVICE_ACCOUNT_EMAIL \
    --key-file-type="json"

# create a secrets manager secret from the key
gcloud secrets create terraform-secret \
    --replication-policy="automatic" \
    --data-file=service_account.json

# List the secret
gcloud secrets list

# verify secret contents ad hoc
gcloud secrets versions access latest --secret="terraform-secret"

# deploy all infrastructure
cd non-prod/us-central1/

terragrunt plan-all

# delete the terragrunt temp dirs
find . -type d -name ".terragrunt-cache" -prune -exec rm -rf {} \;
```

## Notes

terraform keeps overriding state as modules run in parallel to compete for state

## Resources

[Keep your Terraform code DRY](https://terragrunt.gruntwork.io/docs/features/keep-your-terraform-code-dry/)
[Relative Paths](https://community.gruntwork.io/t/relative-paths-in-terragrunt-modules/144/6)
[Handling Dependencies](https://community.gruntwork.io/t/handling-dependencies/315/2)
[Terraform force unlock](https://www.terraform.io/docs/commands/force-unlock.html)
[Third Party Reasons to use terragrunt](https://transcend.io/blog/why-we-use-terragrunt)
[Managing Terraform Secrets](https://blog.gruntwork.io/a-comprehensive-guide-to-managing-secrets-in-your-terraform-code-1d586955ace1)
[Google Provider Documentation](https://www.terraform.io/docs/providers/google/guides/provider_reference.html#full-reference)
