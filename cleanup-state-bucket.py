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


def cleanup_obsolte_states(args):
    repo_actual_blobs = []
    organizaiton = {
        'platform-tf-admin-dev': 'extenda-io',
        'platform-tf-admin-prod': 'extendaretail-com'
    }
    start_path = os.path.join(args.repo, 'organization', organizaiton.get(args.bucket))
    for root, dirs, files in os.walk(start_path):
        if '.terragrunt-cache' not in root:
            is_tf_directory = filter(lambda f: f.endswith('.hcl'), files)
            if is_tf_directory:
                tf_directory = root.replace(start_path,'').strip('/')
                blob_name = os.path.join(tf_directory, 'default.tfstate')
                repo_actual_blobs.append(blob_name)

    storage_client = storage.Client()
    blobs = storage_client.list_blobs(args.bucket)
    for blob in blobs:
        if blob.name.endswith('.tfstate'):
            if blob.name not in repo_actual_blobs:
                if args.dryrun:
                    print('Obsolete state: "%s" (created: %s)' % (blob.name, blob.time_created.date()))
                elif args.noconfirm:
                    blob.delete()
                    print('Obsolete state "%s" (created: %s) deleted' % (blob.name, blob.time_created.date()))
                else:
                    confirm = input('Delete obsolete state "%s" (created: %s) [y/N]? ' % (blob.name, blob.time_created.date())).lower()
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
    parser.add_argument('--bucket', '-b', action='store', help='GCP bucket to cleanup', default='platform-tf-admin-prod')
    parser.add_argument('--repo', '-r', action='store', help='Path to tf-infra-gcp repo', default=os.path.abspath(os.path.join(scriptdir, '../../../')))
    cleanup = parser.add_argument_group(title='Cleanup options')
    cleanup.add_argument('--cleanup-empty', '-e', action='store_true', help='Cleanup empty ("resources": []) state files')
    cleanup.add_argument('--cleanup-obsolete', '-o', action='store_true', help='Cleanup obsolete (no respecting directory in tf-infra-gcp repo) state files')
    cleanup.add_argument('--cleanup-extra', '-x', action='store_true', help='Cleanup extra objects (different to state files)')
    cleanup.add_argument('--cleanup-all', '-a', action='store_true', help='Apply all cleanup (default)')
    args = parser.parse_args(sys.argv[1:])

    if args.cleanup_all:
        args.cleanup_empty = True
        args.cleanup_obsolete = True
        args.cleanup_extra = True

    if (not args.cleanup_empty and not args.cleanup_obsolete and not args.cleanup_extra):
        parser.print_help()
        sys.exit(1)

    if args.cleanup_empty:
        cleanup_empty_states(args)
    if args.cleanup_obsolete:
        cleanup_obsolte_states(args)
    if args.cleanup_extra:
        cleanup_extra_objects(args)


if __name__=="__main__":
    main()
