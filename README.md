# Proton VPN CLI

Copyright (c) 2026 Proton AG

This repository holds the Proton VPN CLI.
For licensing information see [COPYING](COPYING.md) and [LICENSE](LICENSE).
For contribution policy see [CONTRIBUTING](CONTRIBUTING.md).

## Description

The official Proton VPN CLI for Linux.

Current functionality:
- Connect to 19,000+ servers in 139 countries
- Select servers by country, city, or server ID
- Secure Core, P2P, and Tor server support
- Kill switch, NetShield ad-blocker, port forwarding, Custom DNS, IPv6, VPN Accelerator, NAT type
- WireGuard protocol support

Some features and server locations require a paid Proton VPN plan.

Current limitations:
- Cannot run alongside the Proton VPN GUI app
- Headless setups are not currently supported 
- Split tunneling is not yet available

Report issues and request features through [Proton VPN support](https://protonvpn.com/support/contact?subject=%5BCLI%5D&os=Linux&platform=VPN%20for%20Linux).

Have fun on your terminal.

<img src="assets/protonvpn-demo.svg" width="590">

### Cloning

Once you've cloned this repo, run:

> git submodule update --init --recursive

to clone the necessary submodule.

### Installation

You can find the latest release and installation instructions on our [Proton VPN official website](https://protonvpn.com/support/linux-cli).

### Dependencies

For development purposes (within a virtual environment) see the required packages in the setup.py file, under `install_requires` and `extra_require`. As of now these packages will not be available on pypi. Also see [Virtual environment](#virtual-environment) below.

### Virtual environment

If you didn't do it yet, to be able to pip install Proton VPN components you'll
need to set up our internal Python package registry. You can do so running the
command below, after replacing `{GITLAB_TOKEN`} with your
[personal access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)
with the scope set to `api`.

```shell
pip config set global.index-url https://__token__:{GITLAB_TOKEN}@{GITLAB_INSTANCE}/api/v4/groups/{GROUP_ID}/-/packages/pypi/simple
```

You can create the virtual environment and install the rest of dependencies as
follows:

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### CLI misc.

CLI logs are stored under `~/.cache/Proton/VPN/logs/` directory.

User settings are under `~/.config/Proton/VPN/` directory.

## Folder structure

### Folder "debian"

Contains all debian related data, for easy package compilation.

### Folder "rpmbuild"

Contains all rpm/fedora related data, for easy package compilation.

### Folder "proton/vpn/cli"

This folder contains the CLI source code.

### Folder "tests"

This folder contains unit test code.

You can run the tests with:

```shell
pytest
```


## Versioning
Version matches format: `[major][minor][patch]`

We automate the versioning of the debian and rpm files.
All versions of the application are recorded in versions.yml.
To bump the version, add the following text to the top of versions.yml

```yaml
version: <latest version>
time: <date> <time>
author: <your name>
email: <your email address>
urgency: low
stability: unstable
description:
- <A description of the changes this new version contains>
---
```

Make sure you have the '---' dashes at the end of your block of text.
You can use the previous entries as an example.

Finally run `scripts/build_packages.py`. This will generate a new package.spec
file for rpmbuild and a new changelog file for debian.

That's it.

