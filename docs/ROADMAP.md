# LinuxSphere VE — roadmap

This is a **planning document**, not a promise of ship dates. Scope may change following compatibility and security testing.

## 0.2 International — current development baseline

- [x] Install image with BIOS/UEFI boot paths and selectable Hybrid / Manager / Worker / Storage installation roles
- [x] LinuxSphere administrative Cockpit module and host service sources present in the ISO
- [x] Four bundled LinuxSphere UI language packs: EN / DE / FR / ES
- [x] Browser CLI source, host locale controls, guest and node management endpoints present
- [x] SphereFusion, SphereLink, Restic and SafeChange implementation modules present
- [ ] Independent multi-hardware regression report for **v0.2**
- [ ] Published reproducible ISO build pipeline and signed release artifacts

*Checked items above indicate presence in the examined media/code, not production certification.*

## Next — stability and transparent verification

- [ ] Automated ISO build with pinned dependencies, SBOM and provenance
- [ ] Installer matrix: BIOS, UEFI, nested virtualization, network and offline cases
- [ ] Automated VM/container smoke tests, serial and graphical guest console checks
- [ ] Recovery drills: image export, cold restore, off-host backup retrieval
- [ ] Stronger audit trail, credential rotation, API hardening and penetration review
- [ ] Accessible UI states, complete translation coverage and documentation

## Longer-term research

- [ ] Robust interrupted and resumable SphereLink transfers with compatibility guarantees
- [ ] More complete node telemetry, scheduling policies and fault recovery
- [ ] Evaluate production HA prerequisites: membership, quorum, fencing and storage correctness
- [ ] Research feasibility of distributed guest resources; **no transparent cross-host VM RAM is currently implemented**

## Suggested milestones / labels

`type:bug` · `type:feature` · `type:docs` · `area:installer` · `area:ui` · `area:network` · `area:security` · `area:virtualization` · `area:localization` · `status:needs-repro`
