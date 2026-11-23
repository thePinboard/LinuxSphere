# Häufige Fragen

**Ist LinuxSphere ein eigenständig installierbares Betriebssystem?**  
Ja, als Debian-basierte x86-64-Serverinstallation mit eigenen Diensten und Webverwaltung. Der Linux-Kernel und die Debian-Grundarchitektur bleiben erhalten.

**Ist das Dashboard ein normaler Desktop?**  
Nein. Es dient zur Administration von Host, Gästen, Knoten und Backups.

**Ist die Installation offline möglich?**  
Der ISO-Leitfaden beschreibt Offline-Installation und ein mitgeliefertes minimales Container-Testimage. Für zusätzliche Gastimages, Pakete und Updates kann Internetzugang nötig werden. Auf Zielhardware prüfen.

**Welche Sprachen werden unterstützt?**  
Englisch, Deutsch, Französisch und Spanisch. Websprache und Host-Locale sind getrennt einstellbar, eigene Sprachpakete sind vorgesehen.

**Kann ich Windows- und Linux-VMs erstellen?**  
Die x86-VM-Laufzeit ist grundsätzlich generisch. Ob ein konkretes Gastbetriebssystem funktioniert, hängt von Image, Firmware, Treibern, Lizenz und Ressourcen ab. Eine allgemeine Kompatibilitätsfreigabe gibt es nicht.

**Kann eine einzelne VM die RAM-Module mehrerer PCs gleichzeitig nutzen?**  
Nein. SphereFusion verteilt **separate Aufgaben** auf Worker. Die CPU und der RAM einer laufenden VM verbleiben auf ihrem Host.

**Gibt es Live-Migration und automatisches Failover?**  
Nicht als allgemein geprüfte Produktionsfunktion in v0.2.

**Wie ist DroidSphere integriert?**  
Als separate Android-Anwendung mit eigener VM-Laufzeit. Unterstützte ausgeschaltete x86-Gäste können über verschlüsselte SphereLink-Kapseln importiert werden.

**Ist das Projekt produktionsreif oder sicherheitszertifiziert?**  
Nein. Für produktive Freigaben fehlen unter anderem unabhängige Security-Prüfungen, Hardwaretests, Dauerlast- und Recovery-Nachweise.

**Ist es bereits Open Source?**  
Für die eigenen LinuxSphere-Komponenten ist vor dieser Bezeichnung eine eindeutige, geprüfte Lizenz erforderlich. Debian- und Drittsoftware behalten ihre jeweiligen Lizenzen.
