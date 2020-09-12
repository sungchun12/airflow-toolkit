# checkov

Utitilty that runs a static `terraform` code security checks with out of the box tests

- Install the open source package
- Assumes you're running the below commands from the root dir: `airflow-toolkit/`

## How to Run Locally

```bash
# setup python virtual environment locally in unix environment
python3 -m venv py38_venv
source py38_venv/bin/activate
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

- Close out the terminal and start a new one

```bash
# activate the service account
source py38_venv/bin/activate

# checkov -d /user/path/to/iac/code
checkov -d terragrunt_infrastructure_modules/

# only show failed checks
checkov -d terragrunt_infrastructure_modules/ --quiet

# output to json file
checkov -d terragrunt_infrastructure_modules/ -o json > checkov_tests.json
```

## Skip Known Failed Checks

| Check      | Description                                                                                    | Why Skip?                                                                                                                                                                                  | Resolution                                                                           |
| ---------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| CKV_GCP_26 | "Ensure that VPC Flow Logs is enabled for every subnet in a VPC Network"                       | Increases logging costs and for development purposes, may not be necessary. However, if there are integrations with sensitive source systems, this provides additional traffic monitoring. | [Guide](https://docs.bridgecrew.io/docs/bc_gcp_logging_1)                            |
| CKV_GCP_32 | "Ensure 'Block Project-wide SSH keys' is enabled for VM instances"                             | This blocks the ability to ssh via identity aware proxy. Currently, there is no easily programmatic way to limit IAP ssh access to a single VM.                                            | [Guide](https://docs.bridgecrew.io/docs/bc_gcp_networking_8)                         |
| CKV_GCP_38 | "Ensure VM disks for critical VMs are encrypted with Customer Supplied Encryption Keys (CSEK)" | Only needed for an extra security layer as VMs come with default encryption keys.                                                                                                          | [Guide](https://docs.bridgecrew.io/docs/encrypt-boot-disks-for-instances-with-cseks) |

```bash
# skip the specific check expected to fail, but should be examined further for production deployments

checkov -d terragrunt_infrastructure_modules/ --quiet \
  --skip-check CKV_GCP_26,CKV_GCP_32,CKV_GCP_38

```

## Resources

- [CLI Options](https://www.checkov.io/1.Introduction/Getting%20Started.html)

- [Suppress specific checks based on situation](https://github.com/bridgecrewio/checkov/blob/master/docs/2.Concepts/Suppressions.md)

- [Checkov Source](https://github.com/bridgecrewio/checkov)
