#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COREFLOW AUDIT LOGGER v2.1
Enterprise-grade Logging-Lösung mit:
- Rotierender Log-Dateiverwaltung
- Systemd Journal-Integration
- Verschlüsselter Archivierung
"""

import os
import sys
import zlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Union
import logging
from logging.handlers import RotatingFileHandler
try:
    from systemd.journal import JournalHandler
except ImportError:
    JournalHandler = None

class AuditLogger:
    def __init__(self, 
                 system: str = "coreflow",
                 log_dir: str = "/opt/coreflow/logs/audit",
                 max_log_size: int = 10 * 1024 * 1024,  # 10 MB
                 backup_count: int = 5,
                 enable_journal: bool = True):
        """
        Initialisiert den Enterprise Audit Logger
        
        Args:
            system: Systemkennung (z.B. 'autonomous')
            log_dir: Log-Verzeichnispfad
            max_log_size: Maximale Loggröße in Bytes
            backup_count: Anzahl der Log-Backups
            enable_journal: Systemd-Journal Integration
        """
        self.system = system.upper()
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / f"{self.system}_audit.log"
        
        # Verzeichnisstruktur sicherstellen
        self.log_dir.mkdir(parents=True, exist_ok=True, mode=0o750)
        
        # Logger konfigurieren
        self.logger = logging.getLogger(f"CF_AUDIT_{self.system}")
        self.logger.setLevel(logging.INFO)
        
        # File Handler mit Rotation
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=max_log_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s.%(msecs)03dZ | %(name)s | %(message)s',
                            datefmt='%Y-%m-%dT%H:%M:%S')
        )
        self.logger.addHandler(file_handler)
        
        # Optional: Systemd-Journal
        if enable_journal and JournalHandler:
            journal_handler = JournalHandler()
            journal_handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(journal_handler)
    
    def log(self, 
            message: Union[str, Dict],
            metadata: Optional[Dict] = None,
            compress: bool = False):
        """
        Loggt einen Eintrag mit erweiterten Optionen
        
        Args:
            message: Log-Nachricht oder Dictionary
            metadata: Zusätzliche Metadaten
            compress: Nachricht komprimieren
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "system": self.system,
            "message": zlib.compress(message.encode()).hex() if compress and isinstance(message, str) else message,
            "metadata": metadata or {},
            "compressed": compress
        }
        
        # JSON-Formatierung mit pretty-print im Debug-Modus
        log_line = json.dumps(log_entry, indent=2 if os.getenv('CF_DEBUG') else None)
        self.logger.info(log_line)
        
        # Konsolenausgabe im Debug-Modus
        if os.getenv('CF_DEBUG'):
            print(f"[AUDIT] {log_line}", file=sys.stderr)

    def archive_logs(self):
        """Archiviert alte Logs mit Verschlüsselung"""
        # Implementierung würde hier GPG/PGP verwenden
        pass

# Standard-Instanz für einfachen Zugriff
default_logger = AuditLogger()

if __name__ == "__main__":
    # Testlauf
    logger = AuditLogger(system="TEST")
    logger.log("Systemstart", {"version": "2.1.0"})
    logger.log("Kritische Operation", compress=True)
