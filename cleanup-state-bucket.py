#!/usr/bin/env python3

import sys
import os
import argparse
import json
from google.cloud import storage


def cleanup_empty_states(args):
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(args.bucket)
    for blob in blobs:
        if blob.name.endswith('.tfstate') and blob.size < 200: # typicaly empty state file size is 157-159 bytes
            data = json.loads(blob.download_as_string())
            if not data['resources']:
                if args.dryrun:
                    print('Empty state: "%s" (created: %s)' % (blob.name, blob.time_created.date()))
                elif args.noconfirm:
                    blob.delete()
                    print('Empty state "%s" (created: %s) deleted' % (blob.name, blob.time_created.date()))
                else:
                    confirm = input('Delete empty state "%s" (created: %s) [y/N]? ' % (blob.name, blob.time_created.date())).lower()
                    if confirm == 'y':
                        blob.delete()
                        print('Deleted')
                    else:
                        print('Skipped')


def cleanup_orphan_states(args):
    repo_actual_blobs = []
    for root, dirs, files in os.walk(args.root):
        if '.terragrunt-cache' not in root:
            is_tf_directory = filter(lambda f: f.endswith('.hcl'), files)
            if is_tf_directory:
                tf_directory = root.replace(args.root,'').strip('/')
                blob_name = os.path.join(tf_directory, args.suffix, 'default.tfstate')
                repo_actual_blobs.append(blob_name)

    storage_client = storage.Client()
    blobs = storage_client.list_blobs(args.bucket)
    for blob in blobs:
        if blob.name.endswith('.tfstate'):
            if blob.name not in repo_actual_blobs:
                if args.download:
                    data = blob.download_as_string()
                    filepath = os.path.join(args.download, blob.name)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    open(filepath, 'wb').write(data)
                    os.utime(filepath, (blob.time_created.timestamp(), blob.time_created.timestamp()))

                    if args.check_no_instances:
                        no_instances = True
                        jdata = json.loads(data)
                        for res in jdata['resources']:
                            if res['instances']:
                                no_instances = False
                                break
                        if no_instances:
                            print('Has no instances: "%s" (created: %s)' % (blob.name, blob.time_created.date()))

                if args.dryrun:
                    print('Orphan state: "%s" (created: %s)' % (blob.name, blob.time_created.date()))
                elif args.noconfirm:
                    blob.delete()
                    print('Orphan state "%s" (created: %s) deleted' % (blob.name, blob.time_created.date()))
                else:
                    confirm = input('Delete orphan state "%s" (created: %s) [y/N]? ' % (blob.name, blob.time_created.date())).lower()
                    if confirm == 'y':
                        blob.delete()
                        print('Deleted')
                    else:
                        print('Skipped')


def cleanup_extra_objects(args):
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(args.bucket)
    for blob in blobs:
        if not blob.name.endswith('.tfstate'):
            if args.dryrun:
                print('Extra object: "%s" (created: %s)' % (blob.name, blob.time_created.date()))
            elif args.noconfirm:
                blob.delete()
                print('Extra object "%s" (created: %s) deleted' % (blob.name, blob.time_created.date()))
            else:
                confirm = input(
                    'Delete extra object "%s" (created: %s) [y/N]? ' % (blob.name, blob.time_created.date())).lower()
                if confirm == 'y':
                    blob.delete()
                    print('Deleted')
                else:
                    print('Skipped')


def main():
    scriptdir = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser(description='Cleanup terragrunt state GCP bucket', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--dryrun', '-n', action='store_true', help="Don't delete state files, just print it")
    parser.add_argument('--noconfirm', '-y', action='store_true', help="Don't ask confirmation for every object (automatically yes)")
    parser.add_argument('--bucket', '-b', action='store', help='GCP bucket to cleanup', default='')
    parser.add_argument('--root', '-r', action='store', help='Path to terragrunt root folder', default='')
    parser.add_argument('--suffix', '-s', action='store', help="Suffix added to terraform state onject path", default='')
    cleanup = parser.add_argument_group(title='Cleanup options')
    cleanup.add_argument('--cleanup-empty', '-e', action='store_true', help='Cleanup empty ("resources": []) state files')
    cleanup.add_argument('--cleanup-orphan', '-o', action='store_true', help='Cleanup orphan (no respecting directory in terragrunt repo) state files')
    cleanup.add_argument('--cleanup-extra', '-x', action='store_true', help='Cleanup extra objects (other than default.tfstate)')
    cleanup.add_argument('--cleanup-all', '-a', action='store_true', help='Apply all cleanup (default)')
    misc = parser.add_argument_group(title='Misc options')
    misc.add_argument('--download', '-d', action='store', help='Download orphan state files to the directory')
    misc.add_argument('--check-no-instances', '-i', action='store_true', help='Check downloaded files for empty instances (with only schema)')
    templates = parser.add_argument_group(title='Configuration templates')
    template_choice = templates.add_mutually_exclusive_group()
    template_choice.add_argument('--tf-infra-gcp', action='store_true', help="Apply configuration for tf-infra-gcp repo")
    template_choice.add_argument('--common-staging', action='store_true', help="Apply configuration for *-common repo staging bucket")
    template_choice.add_argument('--common-prod', action='store_true', help="Apply configuration for *-common repo prod bucket")
    args = parser.parse_args(sys.argv[1:])

    if args.tf_infra_gcp:
        args.bucket = 'platform-tf-admin-prod'
        args.root = 'organization'

    elif args.common_staging:
        args.bucket = 'tf-state-%s-staging' % os.path.basename(os.getcwd()).replace('-common','')
        args.root = 'infra'
        args.suffix = 'terraform.tfstate'

    elif args.common_prod:
        args.bucket = 'tf-state-%s-prod' % os.path.basename(os.getcwd()).replace('-common','')
        args.root = 'infra'
        args.suffix = 'terraform.tfstate'

    if args.cleanup_all:
        args.cleanup_empty = True
        args.cleanup_orphan = True
        args.cleanup_extra = True

    if (not args.cleanup_empty and not args.cleanup_orphan and not args.cleanup_extra):
        parser.print_help()
        sys.exit(1)

    if args.cleanup_empty:
        cleanup_empty_states(args)
    if args.cleanup_orphan:
        cleanup_orphan_states(args)
    if args.cleanup_extra:
        cleanup_extra_objects(args)


if __name__=="__main__":
    main()
