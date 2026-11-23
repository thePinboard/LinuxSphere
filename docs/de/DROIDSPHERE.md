# DroidSphere × LinuxSphere — Zusammenspiel

**Zwei eigenständige Laufzeitumgebungen mit einer gemeinsamen Schnittstelle.**

| | LinuxSphere VE | DroidSphere VE |
| --- | --- | --- |
| Host | Debian-basierter x86-64-PC/Server | Android-Smartphone/Tablet |
| Laufzeit | QEMU/libvirt-VMs und Incus-Container | Lokale QEMU-VMs innerhalb der Android-App |
| Verwaltung | Cockpit, `dsctl`, SSH, Knoten-API | Android-App, freigegebene HTTPS-/Browser- und SSH-Verwaltung |
| Transfer | Import kompatibler verschlüsselter PC-Kapseln | Export unterstützter ausgeschalteter VMs |
| Projektstand | 0.2 International | 2.0 |

## Ablauf mit SphereLink

1. Auf DroidSphere einen kompatiblen **x86-PC-Gast geordnet ausschalten**.
2. HTTPS-Verwaltung des Mobilgeräts bewusst freigeben und über Fingerabdruck/Code sicher koppeln.
3. VM in einer verschlüsselten `.dscap`-Kapsel bereitstellen und kontrolliert übertragen.
4. LinuxSphere prüft Authentizität, SHA-256-Manifest, Dateiformate und QCOW2-Konsistenz.
5. Auf einem **Worker** oder **Hybrid** eine neue, zunächst ausgeschaltete x86-BIOS-/UEFI-VM erzeugen.

Das Verfahren ist ein **Offline-Import**, keine Live-Migration. Es macht das Handy nicht zum automatisch zuschaltbaren Rechenknoten mit gemeinsamem Arbeitsspeicher.

## Grenzen

Ein ARM64-Android-Gast ist ohne zusätzliche Architektur-/Treiberkompatibilität **nicht** automatisch als x86-PC-Gast verwendbar. Smartphone-Sensorik, Modem und native Grafik-/CPU-Performance werden nicht an die importierte VM garantiert durchgereicht. DroidSphere bleibt ein **separates Projekt** mit eigenem Quellcode, Paket und eigener Dokumentation.
