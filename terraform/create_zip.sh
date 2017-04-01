#!/bin/sh
set -e
test -f ebs-backup.zip && rm -f ebs-backup.zip
zip -j ebs-backup.zip ../ebs-backup.py
