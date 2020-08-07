# cleanup-state-bucket

Helper script to inspect GCP bucket with terraform states and cleanup unused objects.

If intensively work with terraform/terragrunt, that uses remote state on GCP, state bucket become to have large number of extra objects:

- objects representing empty states, i.e. if resources was deleted or terraform was initialized only
- objects representing manually deleted resources, or obsolete state files after reorganizing IaC repoitory
- extra objects, for example old *.tflock files that wasn't remoted correctly

## Usage

```
usage: cleanup-state-bucket.py [-h] [--dryrun] [--noconfirm] [--bucket BUCKET] [--root ROOT] [--suffix SUFFIX] [--cleanup-empty] [--cleanup-orphan] [--cleanup-extra] [--cleanup-all] [--download DOWNLOAD]
                               [--check-no-instances] [--show-uri] [--tf-infra-gcp | --common-staging | --common-prod]

Cleanup terragrunt state GCP bucket

optional arguments:
  -h, --help            show this help message and exit
  --dryrun, -n          Don't delete state files, just print it (default: False)
  --noconfirm, -y       Don't ask confirmation for every object (automatically yes) (default: False)
  --bucket BUCKET, -b BUCKET
                        GCP bucket to cleanup (default: )
  --root ROOT, -r ROOT  Path to terragrunt root folder (default: )
  --suffix SUFFIX, -s SUFFIX
                        Suffix added to terraform state onject path (default: )

Cleanup options:
  --cleanup-empty, -e   Cleanup empty ("resources": []) state files (default: False)
  --cleanup-orphan, -o  Cleanup orphan (no respecting directory in terragrunt repo) state files (default: False)
  --cleanup-extra, -x   Cleanup extra objects (other than default.tfstate) (default: False)
  --cleanup-all, -a     Apply all cleanup (default) (default: False)

Misc options:
  --download DOWNLOAD, -d DOWNLOAD
                        Download orphan state files to the directory (default: None)
  --check-no-instances, -i
                        Check downloaded files for empty instances (with only schema) (default: False)
  --show-uri, -u        Display full uri (gs://*) to the objects (default: False)

Configuration templates:
  --tf-infra-gcp        Apply configuration for tf-infra-gcp repo (default: False)
  --common-staging      Apply configuration for *-common repo staging bucket (default: False)
  --common-prod         Apply configuration for *-common repo prod bucket (default: False)
```
