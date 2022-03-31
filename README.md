<!-- Header block for project -->
<hr>

<div align="center">
    <span style="display:block;text-align:center">
    </span>
    <h1 align="center">Object-Store Abstraction Architecture (Osaka)</h1>
</div>

<pre align="center">
    An abstraction architecture for supporting multiple object-storage systems within HySDS
</pre>

<!-- Header block for project -->

[![](https://circleci.com/gh/hysds/osaka.svg?style=svg)](https://circleci.com/gh/hysds/osaka) ![](https://img.shields.io/github/release-date/hysds/osaka) 
<!-- ☝️ Add badges via: https://shields.io e.g. ![](https://img.shields.io/github/your_chosen_action/your_org/your_repo) ☝️ -->


<!-- ☝️ Screenshot of your software (if applicable) via ![](https://uri-to-your-screenshot) ☝️ -->

Osaka is an object storage abstraction system allowing a user to push generic file objects to various backend storage systems. It was designed to abstract the technological specifics of supporting multiple object stores for the HySDS ecosystem. These different backends are selected based on the scheme element of the URI for the file object, thus can be enacted automatically.  As a minimum requirement, Osaka must have one endpoint that exists on a local file system.

## Features

* Push ability to multiple object-storage systems
* Compatibility with HySDS 
* [INSERT LIST OF FEATURES IMPORTANT TO YOUR USERS HERE]

<!-- ☝️ Replace with a bullet-point list of your features ☝️ -->

### Supported Object-Stores

| Schemes                 | Push Implemented | Pull Implemented | Tested | Notes:                                  |
| ----------------------- | ---------------- | ---------------- | ------ | --------------------------------------- |
| `file://`, `none`       | Yes              | Yes              | Yes    |                                         |
| `s3://`, `s3s://`       | Yes              | Yes              | Yes    |                                         |
| `dav://`, `davs://`     | Yes              | Yes              | Yes    |                                         |
| `http://`, `https://`   | Yes              | Yes              | Yes    |                                         |
| `azure://`, `azures://` | Yes              | Yes              | Yes    | Experimental version by NVG             |
| `ftp://`, `sftp://`     | No               | No               | No     | Needs re-implementation                 |
| `rsync://`              | No               | No               | No     | Not a backend, but a transfer mechanism |
  
## Quick Start

### Requirements

* Python 3
* Access to an object-storage system (e.g. Amazon AWS S3) 
* [INSERT LIST OF REQUIREMENTS HERE]
  
<!-- ☝️ Replace with a bullet-point list of your requirements, including hardware if applicable ☝️ -->

### Setup Instructions

1. [INSERT STEP-BY-STEP SETUP INSTRUCTIONS HERE]
   
<!-- ☝️ Replace with a numbered list of how to set up your software prior to running ☝️ -->

### Run Instructions

1. [INSERT STEP-BY-STEP RUN INSTRUCTIONS HERE, WITH OPTIONAL SCREENSHOTS]

<!-- ☝️ Replace with a numbered list of your run instructions, including expected results ☝️ -->

### Usage Examples

* [INSERT LIST OF COMMON USAGE EXAMPLES HERE, WITH OPTIONAL SCREENSHOTS]

<!-- ☝️ Replace with a list of your usage examples, including screenshots if possible, and link to external documentation for details ☝️ -->

### Test Instructions

Osaka has test scripts available [here](https://github.com/hysds/osaka/tree/develop/osaka/tests)

1. [INSERT STEP-BY-STEP TEST INSTRUCTIONS HERE, WITH OPTIONAL SCREENSHOTS]

<!-- ☝️ Replace with a numbered list of your test instructions, including expected results / outputs with optional screenshots ☝️ -->

## Changelog

See our [releases page](https://github.com/hysds/osaka/releases) for our key versioned releases.

## Frequently Asked Questions (FAQ)

No questions yet. Propose a question to be added here by reaching out to our contributors! See support section below.

## Contributing

1. Create an GitHub issue ticket describing what changes you need (e.g. issue-1)
2. [Fork](https://github.com/hysds/osaka/fork) this repo
3. Make your modifications in your own fork
4. Make a pull-request in this repo with the code in your fork and tag the repo owner / largest contributor as a reviewer

**Working on your first pull request?** See guide: [How to Contribute to an Open Source Project on GitHub](https://kcd.im/pull-request)

## License

See our: [LICENSE](https://github.com/hysds/osaka/blob/develop/LICENSE)

## Support

See our: [contributors](https://github.com/hysds/osaka/graphs/contributors)

Key points of contact are: [@pymonger](https://github.com/pymonger)
