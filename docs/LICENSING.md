# Licensing and redistribution — decision required before public source release

**IMPORTANT:** The publication kit deliberately does **not** place a final `LICENSE` file at repository root. A public repository without an explicit license is not automatically open-source. Do not advertise the project as MIT-licensed until the rights holder makes that choice and checks compatibility with redistributed dependencies.

## Separate the components

1. **Original LinuxSphere source:** identify author/rights holder(s), prior contributors and any code derived from other projects. Choose a suitable license (for example MIT, Apache-2.0 or GPL-family, after a compatibility review).
2. **Debian distribution:** respect upstream package licenses, source availability duties, copyright statements and corresponding license texts. The ISO contains Debian installer and packages beyond the standalone project source.
3. **Bundled third-party JavaScript:** the ISO includes xterm.js and xterm-addon-fit with their own `*.LICENSE` files; preserve attribution and relevant license notices.
4. **Minimal offline container image:** investigate the image's bundled binaries, source and redistribution obligations before publishing it separately.
5. **DroidSphere:** separate project; carry over its own dependency attributions and publishing permissions, rather than automatically applying LinuxSphere's future license.
6. **Brand/media:** confirm ownership and permission for graphics, logos, documentation figures and screenshots before adding them to a public repository.

## A safe release sequence

- Audit source provenance, embedded materials and external dependencies.
- Inventory copyright notices and create a third-party component list (preferably an SBOM for the release image).
- Choose one reviewed license for **original** source files; apply appropriate SPDX headers where needed.
- Preserve mandatory notices and source-distribution obligations for copied third-party components.
- Publish the official license text as `LICENSE` **only after that decision**. The included `LICENSE.MIT.template` is a draft, not operative.
- Add a release description that distinguishes the upstream operating system from independently written LinuxSphere features.

**This document is a publishing checklist, not a legal opinion.**
