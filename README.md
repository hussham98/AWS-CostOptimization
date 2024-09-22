## Documentation
Identifying Stale EBS Snapshots

In this example, we'll create a Lambda function that identifies EBS snapshots that are no longer associated with any active EC2 instance and deletes them to save on storage costs.

## Description
The Lambda function fetches all EBS snapshots owned by the same account ('self') and also retrieves a list of active EC2 instances (running and stopped). For each snapshot, it checks if the associated volume (if exists) is not associated with any active instance. If it finds a stale snapshot, it deletes it, effectively optimizing storage costs.

## Enhancements

- **Scheduled Execution**: The Lambda function is automatically triggered daily using CloudWatch Events.
- **SNS Notifications**: Notifications are sent to an SNS topic whenever a snapshot is deleted, including details of the snapshot and estimated cost savings.
- **Cost Savings Tracking**: For each deleted snapshot, the size is tracked, and an estimated monthly saving (based on $0.05 per GB per month) is calculated and logged.
