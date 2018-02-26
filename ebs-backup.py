# Copyright 2017 Oliver Siegmar
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from datetime import date

import boto3
from dateutil.relativedelta import relativedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ec2 = boto3.resource('ec2')
client = boto3.client('ec2')


def lambda_handler(event, context):
    backup()
    expire()


def backup():
    instances = ec2.instances.filter(Filters=[{'Name': 'tag-key',
                                               'Values': ['LambdaBackupConfiguration']}])
    for instance in instances:
        try:
            backup_instance(instance)
        except:
            logging.exception('Error creating snapshot for {}'.format(instance.id))


def backup_instance(instance):
    instance_tags = dict(map(lambda x: (x['Key'], x['Value']), instance.tags or []))
    instance_name = instance_tags.get('Name', '[unnamed]')
    backup_cfg_str = instance_tags['LambdaBackupConfiguration']

    backup_cfg = parse_config(instance, instance_name, backup_cfg_str)
    backup_label, retention = calc_retention(backup_cfg)

    if not backup_label:
        logger.info('Skip backup of instance {} ({}); LambdaBackupConfiguration is {}'
                    .format(instance.id, instance_name, backup_cfg_str))
        return

    delete_date_fmt = (date.today() + retention).strftime('%Y-%m-%d')
    logger.info('Work on instance {} ({}); Create {} backups to be deleted on {}'
                .format(instance.id, instance_name, backup_label, delete_date_fmt))
    snapshot_ids = []

    for device_mapping in instance.block_device_mappings:
        volume_id = device_mapping['Ebs']['VolumeId']
        device_name = device_mapping['DeviceName']
        logger.info('Create snapshot of volume {} (mounted at {})'.format(volume_id, device_name))
        snapshot = client.create_snapshot(VolumeId=volume_id, Description='Backup of {} {}'
                                          .format(instance_name, device_name))
        snapshot_ids.append(snapshot['SnapshotId'])

    if snapshot_ids:
        logger.info('Create tags for snapshots {}'.format(snapshot_ids))
        tags = {
            'Name': 'lambda-backup',
            'BackupLabel': backup_label,
            'InstanceId': instance.instance_id,
            'InstanceName': instance_name,
            'DeleteOn': delete_date_fmt
        }
        tag_list = list(map(lambda kv: {'Key': kv[0], 'Value': kv[1]}, list(tags.items())))
        client.create_tags(Resources=snapshot_ids, Tags=tag_list)


def parse_config(instance, instance_name, config):
    try:
        backup_configuration = list(map(int, config.split(',')))
        if any(i < 0 for i in backup_configuration):
            raise ValueError('Values must be >= 0')
        return backup_configuration
    except:
        raise ValueError('Syntax error in LambdaBackupConfiguration of {} ({}): {}'
                         .format(instance.id, instance_name, config))


def calc_retention(backup_configuration):
    today = date.today()
    r_daily, r_weekly, r_monthly, r_yearly = backup_configuration
    if today.day == 1:
        if today.month == 1 and r_yearly > 0:
            return 'yearly', relativedelta(years=r_yearly)
        if r_monthly > 0:
            return 'monthly', relativedelta(months=r_monthly)
    if today.weekday() == 6 and r_weekly > 0:
        return 'weekly', relativedelta(weeks=r_weekly)
    if r_daily > 0:
        return 'daily', relativedelta(days=r_daily)
    return None, None


def expire():
    delete_fmt = date.today().strftime('%Y-%m-%d')
    snapshots = ec2.snapshots.filter(OwnerIds=['self'],
                                     Filters=[{'Name': 'tag:DeleteOn', 'Values': [delete_fmt]}])

    for snapshot in snapshots:
        logger.info('Remove snapshot {} (of volume {}) created at {}'
                    .format(snapshot.id, snapshot.volume_id, snapshot.start_time))
        snapshot.delete()
