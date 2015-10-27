keydom
======

[![Build Status](https://ci.maio.me/api/badge/github.com/pirogoeth/keydom/status.svg?branch=master)](https://ci.maio.me/github.com/pirogoeth/keydom)

Keydom is a project that is being written with the intent of storing public keys (SSH, GPG, etc).

Right now, only the API server is in progress. Later on, a CLI and potentially a Web UI will be introduced.
This is still alpha software and is nowhere near ready for production.

Technologies:
- [Bottle](http://bottlepy.org)
- [Malibu](https://phabricator.ramcloud.io/project/view/2/)
- [Peewee ORM](http://peewee-orm.com)
- [Rest API Template](https://phabricator.ramcloud.io/diffusion/RAT/)
- [Newman](https://github.com/postmanlabs/newman)
- Some others...


Roadmap
=======

- [ ] Stablize the API
- [ ] Get functional and unit tests (nose) written
- [ ] Extend Newman tests to match the full API
- [ ] Better search support


Contributing
============

Feedback, comments, and PRs would be extremely appreciated. We try to follow most of the Python
standards, but there are some other stylistic things that aren't adhered to very strongly.

Style:
- Spaces, no tabs
- tabstop=4 softtabstop=4 shiftwidth=4
- 80 character hard wrap
- Single indent past previous on wrapped lines

To discuss code or anything else, you can find us on IRC at irc.maio.me in #dev.


Licensing
=========

This project is licensed under the MIT License. You can view the full terms of the license in `/LICENSE.txt`.
