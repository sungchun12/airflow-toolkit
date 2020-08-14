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

# setup permissions to run terragrunt operations
export PROJECT_ID="wam-bam-258119"
gcloud auth activate-service-account --key-file=service_account.json

# deploy all infrastructure
cd non-prod/us-central1/

terragrunt plan-all

```

## Post-Deployment Instructions

```bash
# Error: Error waiting to create Environment: Error waiting to create Environment: Error waiting for Creating Environment: error while retrieving operation: Get "https://composer.googleapis.com/v1beta1/projects/wam-bam-258119/locations/us-central1/operations/de094856-fea7-4ac4-824f-691b6cb42838?alt=json&prettyPrint=false": EOF. An initial environment was or is still being created, and clean up failed with error: Getting creation operation state failed while waiting for environment to finish creating, but environment seems to still be in 'CREATING' state. Wait for operation to finish and either manually delete environment or import "projects/wam-bam-258119/locations/us-central1/environments/dev-composer" into your state.

# add secrets manager IAM policy binding to composer service account
PROJECT_ID="wam-bam-258119"
MEMBER_SERVICE_ACCOUNT_EMAIL="serviceAccount:composer-sa-dev@wam-bam-258119.iam.gserviceaccount.com"
SECRET_ID="airflow-conn-secret"

gcloud secrets add-iam-policy-binding $SECRET_ID \
    --member=$MEMBER_SERVICE_ACCOUNT_EMAIL \
    --role="roles/secretmanager.secretAccessor"

# gcloud projects add-iam-policy-binding $PROJECT_ID \
#   --member=$MEMBER_SERVICE_ACCOUNT_EMAIL \
#   --role="roles/storage.objectAdmin"

# gcloud projects add-iam-policy-binding $PROJECT_ID \
#   --member=$MEMBER_SERVICE_ACCOUNT_EMAIL \
#   --role="roles/container.clusterAdmin"

# https://stackoverflow.com/questions/60359125/kubernetespodoperator-not-recognizing-the-service-account-name
# https://stackoverflow.com/questions/55498599/how-to-set-proper-permissions-to-run-kubernetespodoperator-in-cloud-composer
# https://cloud.google.com/container-registry/docs/access-control#grant
# kubectl auth can-i create pods -n default--as=system:serviceaccount:composer-1-11-2-airflow-1-10-9-de094856:default

# https://cloud.google.com/composer/docs/how-to/managing/creating#gcloud

# specific permission to container registry bucket
gsutil iam ch $MEMBER_SERVICE_ACCOUNT_EMAIL:objectAdmin gs://artifacts.wam-bam-258119.appspot.com/

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
[Installing Homebrew in GitHub Actions](https://github.community/t/installing-homebrew-on-linux/17994)
