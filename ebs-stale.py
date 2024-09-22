import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    sns = boto3.client('sns')
    sns_topic_arn = 'arn:aws:sns:your-region:your-account-id:EBS-Snapshot-Deletion'  # replace with your SNS Topic ARN


    # Get all EBS snapshots
    response = ec2.describe_snapshots(OwnerIds=['self'])

    # Get all active EC2 instance IDs
    instances_response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    active_instance_ids = set()

    for reservation in instances_response['Reservations']:
        for instance in reservation['Instances']:
            active_instance_ids.add(instance['InstanceId'])

    total_savings = 0

    # Iterate through each snapshot and delete if it's not attached to any volume or the volume is not attached to a running instance
    for snapshot in response['Snapshots']:
        snapshot_id = snapshot['SnapshotId']
        volume_id = snapshot.get('VolumeId')
        snapshot_size = snapshot['VolumeSize']  # Get the size of the snapshot in GB

        if not volume_id:
            # Delete the snapshot if it's not attached to any volume
            ec2.delete_snapshot(SnapshotId=snapshot_id)
            print(f"Deleted EBS snapshot {snapshot_id} as it was not attached to any volume.")
            savings = snapshot_size * 0.05  # Assume $0.05 per GB per month
            total_savings += savings
            sns.publish(
                TopicArn=sns_topic_arn,
                Message=f"Deleted EBS snapshot {snapshot_id}. Estimated cost saving: ${savings:.2f} per month.",
                Subject='EBS Snapshot Deletion Notification'
            )
        else:
            # Check if the volume still exists
            try:
                volume_response = ec2.describe_volumes(VolumeIds=[volume_id])
                if not volume_response['Volumes'][0]['Attachments']:
                    ec2.delete_snapshot(SnapshotId=snapshot_id)
                    print(f"Deleted EBS snapshot {snapshot_id} as it was taken from a volume not attached to any running instance.")
                    savings = snapshot_size * 0.05  # Assume $0.05 per GB per month
                    total_savings += savings
                    sns.publish(
                        TopicArn=sns_topic_arn,
                        Message=f"Deleted EBS snapshot {snapshot_id}. Estimated cost saving: ${savings:.2f} per month.",
                        Subject='EBS Snapshot Deletion Notification'
                    )
            
            except ec2.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'InvalidVolume.NotFound':
                    # The volume associated with the snapshot is not found (it might have been deleted)
                    ec2.delete_snapshot(SnapshotId=snapshot_id)
                    print(f"Deleted EBS snapshot {snapshot_id} as its associated volume was not found.")
                    savings = snapshot_size * 0.05  # Assume $0.05 per GB per month
                    total_savings += savings
                    sns.publish(
                        TopicArn=sns_topic_arn,
                        Message=f"Deleted EBS snapshot {snapshot_id}. Estimated cost saving: ${savings:.2f} per month.",
                        Subject='EBS Snapshot Deletion Notification'
                    )

    # Final message with total savings
    sns.publish(
        TopicArn=sns_topic_arn,
        Message=f"Total cost savings from deleted snapshots: ${total_savings:.2f} per month.",
        Subject='Monthly EBS Snapshot Deletion Cost Savings'
    )
