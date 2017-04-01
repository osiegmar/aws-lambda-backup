resource "aws_iam_role" "lambda_ebs_backup" {
    name = "lambda_ebs_backup"

    assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "lambda_ebs_backup_policy" {
    name = "lambda_ebs_backup_policy"
    role = "${aws_iam_role.lambda_ebs_backup.id}"

    policy = <<EOF
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
EOF
}

resource "aws_lambda_function" "lambda_ebs_backup" {
    filename = "ebs-backup.zip"
    function_name = "ebs-backup"
    role = "${aws_iam_role.lambda_ebs_backup.arn}"
    handler = "ebs-backup.lambda_handler"
    source_code_hash = "${base64sha256(file("ebs-backup.zip"))}"
    runtime = "python2.7"
    timeout = 60
}

resource "aws_cloudwatch_event_rule" "lambda_ebs_backup" {
    name = "lambda_ebs_backup"
    description = "Run backups once a day"
    schedule_expression = "rate(1 day)"
}

resource "aws_cloudwatch_event_target" "lambda_ebs_backup" {
    rule = "${aws_cloudwatch_event_rule.lambda_ebs_backup.name}"
    target_id = "ebs-backup"
    arn = "${aws_lambda_function.lambda_ebs_backup.arn}"
}

resource "aws_lambda_permission" "lambda_ebs_backup" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = "${aws_lambda_function.lambda_ebs_backup.function_name}"
    principal = "events.amazonaws.com"
    source_arn = "${aws_cloudwatch_event_rule.lambda_ebs_backup.arn}"
}
