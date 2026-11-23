# LinuxSphere VE 0.2 — Installationsanleitung

> Für **Test- und Entwicklungsumgebungen**. Wichtige Daten vorher sichern: Die Installation kann das gewählte Zielmedium vollständig überschreiben.

## Voraussetzungen

- x86-64-PC, Server oder Test-VM mit BIOS- oder UEFI-Boot.
- Planungswert: **2 logische CPUs, 4 GiB RAM, 20 GiB Systemdatenträger**; zusätzlicher Platz für VM-Datenträger, Container und Backups.
- Für Hardwarebeschleunigung: Intel VT-x bzw. AMD-V und nutzbarer KVM-Zugriff. Ohne KVM ist der QEMU-Softwarepfad potenziell deutlich langsamer.
- Vertrauenswürdiges LAN, Host-Benutzerkonto und bevorzugt kabelgebundene Netzwerkanbindung.

## ISO vorbereiten

Die Datei `LinuxSphere-VE-0.2-International-amd64.iso` nach Erstellung des GitHub-Releases herunterladen und mit der [SHA-256-Prüfsumme](../RELEASE_ASSET_SHA256.txt) abgleichen:

```powershell
Get-FileHash .\LinuxSphere-VE-0.2-International-amd64.iso -Algorithm SHA256
```

Für eine Test-VM die ISO als virtuelles CD/DVD-Medium einbinden. Für physische Tests auf einen dedizierten, entbehrlichen USB-Stick schreiben. Ein Image-Schreibvorgang löscht dessen bisherigen Inhalt.

## Installation

1. Vom Medium im **BIOS- oder UEFI-Modus** starten.
2. Für einen Einzelserver **Install Hybrid** auswählen; alternativ Manager, Worker oder Storage gemäß Netzwerkplanung.
3. Sprache, Land, Tastatur, Hostname und Host-Benutzer festlegen.
4. Ziellaufwerk und Änderungen an der Partitionstabelle nochmals genau prüfen.
5. Installation abschließen, Medium entfernen und den neuen Host starten.

## Webkonsole

IP mit `ip -br a` am Host anzeigen lassen und über das lokale Netzwerk zugreifen:

```text
https://SERVER-IP:9090/linuxsphere
```

Bei einem selbst ausgestellten Zertifikat den Fingerabdruck über einen vertrauenswürdigen Weg prüfen. Mit dem Installationsbenutzer anmelden. Für administrative Änderungen die Cockpit-Adminfreigabe verwenden. Managementports nicht direkt im Internet freigeben.

## Erste Schritte

- Im **Dashboard** CPU, RAM, Datenträger, Gaststatus und KVM-Verfügbarkeit ansehen.
- Unter **Guests** eine VM mit ISO/QCOW2 oder einen Incus-Container erzeugen.
- Im Menü **CLI** ein interaktives Host-Terminal starten; z. B. `sudo virsh -c qemu:///system list --all`.
- Unter **Language** Browseroberfläche und Host-Locale getrennt konfigurieren.
- Weitere Knoten unter **Nodes** mittels kurzlebigem Einladungscode koppeln.
- Eine ausgeschaltete Test-VM sichern, unter neuem Namen wiederherstellen und tatsächlich starten.

## Netzwerk und Administration

| Dienst | Standardport | Sicherheit |
| --- | --- | --- |
| Cockpit-Webverwaltung | HTTPS 9090/TCP | Nur LAN/VPN |
| Knoten-API | HTTPS 9443/TCP | Nur autorisierte Knoten |
| SSH/SFTP | 22/TCP | Schlüsselbasierte Anmeldung und Einschränkungen |
| Gastkonsole | VNC lokal am Host | Nicht direkt öffentlich öffnen |

```bash
sudo dsctl status
sudo dsctl nodes
sudo dsctl invite
sudo dsctl --help
sudo virsh -c qemu:///system list --all
sudo incus list
sudo nmtui
journalctl -u linuxsphere-api -u linuxsphere-compute
```

## Grenzen

Keine generelle Abnahme für Produktionssysteme, keine garantierte Live-Migration oder automatisches Cluster-Failover und **kein transparenter gemeinsamer RAM einer einzelnen VM über mehrere Hosts**. Backups sind erst nach erfolgreichem Restore-Test belastbar.
