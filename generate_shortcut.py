#!/usr/bin/env python3
"""
PayPal → Banking Kalender Kurzbefehl
Nur Standard-Shortcuts-Actions (keine Mail-spezifischen)
Funktioniert auf iOS 16+ / iOS 26+
"""
import plistlib, uuid

def uid(): return str(uuid.uuid4()).upper()

U    = "￼"   # Placeholder für Variablen in Shortcuts-Text
DASH = "–"   # En-Dash

AM_UUID   = uid()
AM_I_UUID = uid()
ME_UUID   = uid()
ME_I_UUID = uid()
TI_UUID   = uid()
NO_UUID   = uid()
RE_UUID   = uid()

def var(name):
    return {"Value": {"Type": "Variable", "VariableName": name},
            "WFSerializationType": "WFTextTokenAttachment"}

def out(label, u):
    return {"Value": {"Type": "ActionOutput", "OutputName": label, "OutputUUID": u},
            "WFSerializationType": "WFTextTokenAttachment"}

def tok(s, r):
    return {"Value": {"string": s, "attachmentsByRange": r},
            "WFSerializationType": "WFTextTokenString"}

# "PayPal – {Haendler} – {Betrag}"
# P(0)a(1)y(2)P(3)a(4)l(5) (6)–(7) (8)▯(9) (10)–(11) (12)▯(13)
title_str = f"PayPal {DASH} {U} {DASH} {U}"
title_r   = {
    "{9, 1}":  {"Type": "Variable", "VariableName": "Haendler"},
    "{13, 1}": {"Type": "Variable", "VariableName": "Betrag"},
}

# "PayPal Zahlung\nBetrag: ▯\nHändler: ▯"
# P…g(13)\n(14)B…g(20):(21) (22)▯(23)\n(24)H(25)ä(26)n(27)d(28)l(29)e(30)r(31):(32) (33)▯(34)
notes_str = f"PayPal Zahlung\nBetrag: {U}\nHändler: {U}"
notes_r   = {
    "{23, 1}": {"Type": "Variable", "VariableName": "Betrag"},
    "{34, 1}": {"Type": "Variable", "VariableName": "Haendler"},
}

# "✅ Eintrag erstellt!\n▯ – ▯"
# ✅(0) (1)E…t(17)!(18)\n(19)▯(20) (21)–(22) (23)▯(24)
res_str = f"✅ Eintrag erstellt!\n{U} {DASH} {U}"
res_r   = {
    "{20, 1}": {"Type": "Variable", "VariableName": "Haendler"},
    "{24, 1}": {"Type": "Variable", "VariableName": "Betrag"},
}

actions = [
    # 1. Mail-Eingabe als Variable speichern (direkte Text-Koercion bei späteren Actions)
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {"WFVariableName": "MailMsg"}
        # kein WFInput → verwendet Shortcut-Input (die Mail)
    },

    # 2. Betrag suchen: "29,99 EUR" / "29,99€" / "EUR 29,99"
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.matchtext",
        "WFWorkflowActionParameters": {
            "UUID": AM_UUID,
            "WFMatchTextPattern": r"\d[\d.]*[.,]\d{2}\s*(?:EUR|€)",
            "WFMatchTextCaseSensitive": False,
            "WFInput": var("MailMsg")   # Mail wird zu Text koerziert (Body)
        }
    },

    # 3. Ersten Betrag-Treffer
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
        "WFWorkflowActionParameters": {
            "UUID": AM_I_UUID,
            "WFItemSpecifier": "First Item",
            "WFInput": out("Matches", AM_UUID)
        }
    },

    # 4. Variable "Betrag"
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "Betrag",
            "WFInput": out("Item from List", AM_I_UUID)
        }
    },

    # 5. Händler suchen: Text nach "an " vor "gesendet/bezahlt/genehmigt"
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.matchtext",
        "WFWorkflowActionParameters": {
            "UUID": ME_UUID,
            "WFMatchTextPattern": r"(?<=\ban )([^\n\r]+?)(?= gesendet| bezahlt| genehmigt|\n|\r|$)",
            "WFMatchTextCaseSensitive": False,
            "WFInput": var("MailMsg")
        }
    },

    # 6. Ersten Händler-Treffer
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
        "WFWorkflowActionParameters": {
            "UUID": ME_I_UUID,
            "WFItemSpecifier": "First Item",
            "WFInput": out("Matches", ME_UUID)
        }
    },

    # 7. Variable "Haendler"
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "Haendler",
            "WFInput": out("Item from List", ME_I_UUID)
        }
    },

    # 8. Titel-Text: "PayPal – Haendler – Betrag"
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "UUID": TI_UUID,
            "WFTextActionText": tok(title_str, title_r)
        }
    },

    # 9. Notizen-Text
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "UUID": NO_UUID,
            "WFTextActionText": tok(notes_str, notes_r)
        }
    },

    # 10. Kalender-Eintrag in "Banking", ganztägig, heute
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.addnewevent",
        "WFWorkflowActionParameters": {
            "WFCalendarItemTitle": out("Text", TI_UUID),
            "WFCalendarItemCalendar": "Banking",
            "WFCalendarItemAllDay": True,
            "WFCalendarItemNotes": out("Text", NO_UUID),
        }
    },

    # 11. Ergebnis anzeigen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.showresult",
        "WFWorkflowActionParameters": {
            "UUID": RE_UUID,
            "Text": tok(res_str, res_r)
        }
    },
]

shortcut = {
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowClientVersion": "1140.1",
    "WFWorkflowTypes": [],
    "WFWorkflowHasShortcutInputVariables": True,
    "WFWorkflowInputContentItemClasses": ["WFMailMessageContentItem"],
    "WFWorkflowIcon": {
        "WFWorkflowIconStartColor": 946986751,
        "WFWorkflowIconGlyphNumber": 59503
    },
    "WFWorkflowActions": actions
}

out_path = "/home/user/Aidy/PayPal_Banking_Kalender.shortcut"
with open(out_path, "wb") as f:
    plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)

import os
print(f"OK: {out_path}  ({os.path.getsize(out_path)} Bytes, {len(actions)} Aktionen)")
