# LinuxSphere auf GitHub veröffentlichen — Anleitung

## Welche Dateien kommen wohin?

- **Repository (`LinuxSphere`)**: `README.md` (Englisch als Startseite), `README.de.md`, `docs/`, `.github/`, `src/`, `CHANGELOG.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`, `.gitignore`.
- **GitHub Release (`v0.2.0`)**: die **Originaldatei** `LinuxSphere-VE-0.2-International-amd64.iso` als Download-Anhang plus Beschreibung aus `docs/RELEASE_NOTES_v0.2.md`.
- **Nicht ins Repository hochladen**: komplette ISO, private Schlüssel, Passwörter, Host-Token, echte Gastdatenträger oder persönliche Backups.

## Direkter Ablauf in GitHub

1. Auf GitHub ein neues Repository **`LinuxSphere`** erstellen. Kurzbeschreibung und Topics aus `GITHUB_COPY_PASTE_METADATA.md` übernehmen. Bei einem öffentlichen Repository besonders die Lizenz-/Urheberrechtslage vorher prüfen.
2. Die Dateien aus diesem Paket mit **gleicher Ordnerstruktur** hochladen. GitHub erkennt automatisch `README.md`, `CONTRIBUTING.md`, `SECURITY.md` und Issue-Formulare.
3. Vor Veröffentlichung `src/` und alle Abhängigkeiten auf **Lizenzen, Copyright, Secrets und vertrauliche Daten** prüfen. Die vorhandene `LICENSE.MIT.template` ist **keine aktive Lizenz**. Bei getroffener und geprüfter Entscheidung die passende vollständige Lizenz als `LICENSE` anlegen.
4. Unter **Releases → Draft a new release** den Tag `v0.2.0` und den Titel `LinuxSphere VE 0.2 International — Development Preview` verwenden, **Set as a pre-release** aktivieren und die Original-ISO als Release-Asset hochladen.
5. SHA-256 der hochgeladenen ISO mit `docs/RELEASE_ASSET_SHA256.txt` vergleichen. Bei abweichendem Hash die Release-Notizen aktualisieren oder die unveränderte Original-ISO verwenden.
6. Im Repository unter **Settings → Security & analysis** nach Möglichkeit **Private vulnerability reporting** aktivieren. `SECURITY.md` bleibt dann direkt passend.
7. README-Links und Mermaid-Diagramme auf GitHub visuell prüfen; anschließend Issues, Diskussionen und reale Testdaten pflegen.

## Warum die ISO nicht in Git?

Die geprüfte ISO ist `492830720` Byte groß (~470 MiB). GitHub blockiert reguläre Git-Dateien über 100 MiB; Release-Assets eignen sich dagegen für separate Downloads. Bewahre die Versionsdatei außerhalb der Git-Historie auf. Die Release-Datei muss vor Freigabe ebenfalls auf rechtliche Weiterverteilbarkeit geprüft werden.

## Was dieses Paket noch NICHT ersetzt

Es enthält Dokumentation und einen aus der ISO extrahierten Snapshot der LinuxSphere-Projektquellen, **aber keine komplett reproduzierbare ISO-Build-Pipeline**, keine Produktionsfreigabe und keine abgeschlossene Prüfung aller Debian-/Drittsoftwarelizenzen. Bewusst keine erfundenen GitHub-Links, E-Mail-Adressen, Benchmarks oder Testzertifikate.
