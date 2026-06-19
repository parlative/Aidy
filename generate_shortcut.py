#!/usr/bin/env python3
"""
PayPal Banking Kalender Kurzbefehl – Finale Version
Für macOS Import → iCloud Sync → iPhone
"""
import plistlib, uuid

def uid(): return str(uuid.uuid4()).upper()
U = "￼"; DASH = "–"

BODY_UUID = uid()
AM_UUID = uid(); AM_I = uid()
ME_UUID = uid(); ME_I = uid()
DT_UUID = uid(); DT_I = uid()
DATE_UUID = uid()

def var(name):
    return {"Value": {"Type": "Variable", "VariableName": name},
            "WFSerializationType": "WFTextTokenAttachment"}

def out(label, u):
    return {"Value": {"Type": "ActionOutput", "OutputName": label, "OutputUUID": u},
            "WFSerializationType": "WFTextTokenAttachment"}

def tok(s, r):
    return {"Value": {"string": s, "attachmentsByRange": r},
            "WFSerializationType": "WFTextTokenString"}

# Titel: "PayPal – {Haendler} – {Betrag} | {DatumText}"
# P(0)a(1)y(2)P(3)a(4)l(5) (6)–(7) (8)▯(9) (10)–(11) (12)▯(13) (14)|(15) (16)▯(17)
title = tok(f"PayPal {DASH} {U} {DASH} {U} | {U}", {
    "{9, 1}":  {"Type": "Variable", "VariableName": "Haendler"},
    "{13, 1}": {"Type": "Variable", "VariableName": "Betrag"},
    "{17, 1}": {"Type": "Variable", "VariableName": "DatumText"},
})

# Notizen: "Betrag: ▯\nHändler: ▯\nFällig: ▯"
# B…:(6) (7)▯(8)\nH(10)ä(11)n(12)d(13)l(14)e(15)r(16):(17) (18)▯(19)\nF(21)ä(22)l(23)l(24)i(25)g(26):(27) (28)▯(29)
notes = tok(f"Betrag: {U}\nHändler: {U}\nFällig: {U}", {
    "{8, 1}":  {"Type": "Variable", "VariableName": "Betrag"},
    "{19, 1}": {"Type": "Variable", "VariableName": "Haendler"},
    "{29, 1}": {"Type": "Variable", "VariableName": "DatumText"},
})

actions = [
    # 1. Mail-Eingabe als Variable speichern
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {"WFVariableName": "MailMsg"}
    },
    # 2. Text aus der Mail abrufen (Body)
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "UUID": BODY_UUID,
            "WFInput": var("MailMsg")
        }
    },
    # 3. Body als Variable speichern
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "MailBody",
            "WFInput": out("Text", BODY_UUID)
        }
    },
    # 4. Betrag suchen: "146,43 €" oder "146,43 EUR"
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.text.match",
        "WFWorkflowActionParameters": {
            "UUID": AM_UUID,
            "WFMatchTextPattern": r"\d[\d.]*[.,]\d{2}\s*(?:€|EUR)",
            "WFMatchTextCaseSensitive": False,
            "WFInput": var("MailBody")
        }
    },
    # 5. Ersten Treffer nehmen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
        "WFWorkflowActionParameters": {
            "UUID": AM_I, "WFItemSpecifier": "First Item",
            "WFInput": out("Matches", AM_UUID)
        }
    },
    # 6. Variable Betrag
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "Betrag",
            "WFInput": out("Item from List", AM_I)
        }
    },
    # 7. Händler suchen: "bei K&K Getränke GmbH für..."
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.text.match",
        "WFWorkflowActionParameters": {
            "UUID": ME_UUID,
            "WFMatchTextPattern": r"(?<=\bbei )([^\n\r]+?)(?= für| –| Bezahlung|\n|\r|$)",
            "WFMatchTextCaseSensitive": False,
            "WFInput": var("MailBody")
        }
    },
    # 8. Ersten Treffer nehmen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
        "WFWorkflowActionParameters": {
            "UUID": ME_I, "WFItemSpecifier": "First Item",
            "WFInput": out("Matches", ME_UUID)
        }
    },
    # 9. Variable Haendler
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "Haendler",
            "WFInput": out("Item from List", ME_I)
        }
    },
    # 10. Fälligkeitsdatum suchen: "18. Juli 2026"
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.text.match",
        "WFWorkflowActionParameters": {
            "UUID": DT_UUID,
            "WFMatchTextPattern": r"\d{1,2}\. \w+ \d{4}",
            "WFMatchTextCaseSensitive": False,
            "WFInput": var("MailBody")
        }
    },
    # 11. Ersten Treffer nehmen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
        "WFWorkflowActionParameters": {
            "UUID": DT_I, "WFItemSpecifier": "First Item",
            "WFInput": out("Matches", DT_UUID)
        }
    },
    # 12. Variable DatumText
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "DatumText",
            "WFInput": out("Item from List", DT_I)
        }
    },
    # 13. Aktuelles Datum holen (für Startdatum des Kalendereintrags)
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.date",
        "WFWorkflowActionParameters": {"UUID": DATE_UUID}
    },
    # 14. Kalender-Eintrag erstellen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.addnewevent",
        "WFWorkflowActionParameters": {
            "WFCalendarItemTitle": title,
            "WFCalendarItemCalendar": "Banking",
            "WFCalendarItemAllDay": True,
            "WFCalendarItemStartDate": out("Current Date", DATE_UUID),
            "WFCalendarItemNotes": notes,
        }
    },
]

shortcut = {
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowClientVersion": "1140.1",
    "WFWorkflowTypes": [],
    "WFWorkflowHasShortcutInputVariables": True,
    "WFWorkflowInputContentItemClasses": ["WFMailMessageContentItem"],
    "WFWorkflowIcon": {"WFWorkflowIconStartColor": 946986751, "WFWorkflowIconGlyphNumber": 59503},
    "WFWorkflowActions": actions
}

path = "/home/user/Aidy/PayPal_Banking_Kalender.shortcut"
with open(path, "wb") as f:
    plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)

import os; print(f"OK: {path}  ({os.path.getsize(path)} B, {len(actions)} Aktionen)")
