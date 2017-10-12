Object-Store Abstraction ? Architecture (Osaka)
===============================================

Osaka is an object storage abstraction system allowing the user to push generic file object to various backend storage system.  These different backends are selected based on the scheme element of the URI for the file.  Currently, Osaka must have one endpoin exist on the local file system.

| Schemes | Push Implemented | Pull Implemented | Tested | Notes: |
| ------- | ---------------- | ---------------- |--------|---------------------------------|
| file://,none  | Yes | Yes | Yes | |
| s3://,s3s://  | Yes | Yes | Yes | |
| dav://,davs://  | Yes | Yes | Yes | |
| http://,https://| Yes | Yes | Yes | |
| azure://,azures:// | No | No | No | Needs reimplmenetation, no dev azure instance exists |
| ftp://,sftp://  | No | No | No | Needs reimplmentation |
| rsync:// | No | No |No | Not a backend, but a transfer mechanism |


