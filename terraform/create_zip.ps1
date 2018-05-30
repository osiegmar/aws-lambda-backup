$ParentDirectory = Get-Item ..
$origin = Join-Path $ParentDirectory "ebs-backup.py"
$Directory = Get-Item .
$destination = Join-Path $Directory "ebs-backup.zip"
if (test-path $destination) { 
  echo "Zip file already exists at $destination" 
  return 
}
Add-Type -assembly "System.IO.Compression.FileSystem"
Compress-Archive -Path $origin -DestinationPath $destination;