# AWS Lambda Backup

AWS Lambda Backup is a script to create and remove snapshots of EBS volumes. 


## Features

- Create daily, weekly, monthly and yearly snapshots based on your individual configuration
- Automatically clean up old snapshots



## Configuration

Just add a Tag named LambdaBackupConfiguration to your EC2 instances with the following format:

`[RetentionDaily],[RetentionWeekly],[RetentionMonthly],[RetentionYearly]`

Examples:
- `7,4,12,1` to have 7 daily, 4 weekly, 12 monthly and 1 yearly backup
- `7,0,3,0` to have 7 daily, 3 monthly backups
- `0,4,0,0` to have 4 weekly backups

Only one backup per day will be created (due to parallel snapshot limitations of AWS).
Weekly backups will be created on Sunday, monthly backups on 1st day of the month and yearly
backups on 1st of January.
If you specify 0 for a weekly, monthly or yearly Retention, a backup for the next group
(monthly instead of yearly, weekly instead of monthly and daily instead of weekly) will be made.


## Installation

### Via Terraform
```sh
cd terraform
./create_zip.sh
terraform plan -out terraform.tfplan
```

Check if everything is ok and then call:

```sh
terraform apply terraform.tfplan
```


### Via CloudFormation

TBD

### Manually

1) Create an IAM role for AWS Lambda and add the following inline policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateSnapshot",
                "ec2:CreateTags",
                "ec2:DeleteSnapshot",
                "ec2:DescribeInstances",
                "ec2:DescribeSnapshots"
            ],
            "Resource": "*"
        }
    ]
}
```

2) Create a Lambda function

* Select blueprint
    * Select "Blank Function"
* Configure triggers
    * Select "CloudWatch Events - Schedule"
    * Choose "rate(1 day)"
    * Enable trigger
* Configure function
    * Enter name
    * Select "Python 2.7" from the Runtime dropdown
    * Copy the source code from ebs-backup.py to code window
    * Check that Handler is "lambda_function.lambda_handler"
    * Choose the previously created IAM role
     
3) Check the logs

Check the logs in the CloudWatch Logs area.

## Copyright

Copyright 2017 Oliver Siegmar

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
