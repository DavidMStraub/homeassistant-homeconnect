# Contributing to the Home Connect Beta repository

First of all, thanks that you are considering to contribute through an issue or pull request! :+1:

These are a few guidelines to simplify collaboration on this project.

## The role of this repository

Please note that the original custom integration called `homeconnect` has been merged (renamed to `home_connect`) into Home Assistant Core as of version 0.110. This repository contains a custom integration `home_connect_beta` which is meant for developing and beta testing new features.

**Of couse, you are free to contribute your improvements also directly to Home Assistant Core**, if you have tested them extensively yourself.

## Guidelines for issues

Please *do not* submit issues about:

- **Authentication/authorization.** If you suspect it to be a configuration problem, please open a thread (or find an existing one) in the [Home Assistant Community](https://community.home-assistant.io/) forum. If you suspect it to be a bug (that is not caused by one of the beta changes in this repo), please submit an issue to [Home Assistant Core](https://github.com/home-assistant/core/issues).
- **Bugs** that you have observed in the **official integration**. Please submit them as issues to [Home Assistant Core](https://github.com/home-assistant/core/issues).

Please *do* submit issues about:

- **Feature requests**. Please do look for existing feature request issues first.
- **Bugs** that you suspect have been caused by changes in this **beta version** (e.g. because you do not observe them when using the official integration).

## Guidelines for pull requests

Pull requests are always welcome :+1: However the maintainer of this repository might be sluggish in his response. To speed-up the process, please

- Only submit atomic changes (one feature at a time).
- If there is no existing feature request, please consider opening a feature request issue first.
- Try to stick to the code formatting rules of Home Assistant Core (black etc.). If you are unsure, never mind, we will manage.

Again, you are of course welcome to also submit your work directly to Home Assistant Core!