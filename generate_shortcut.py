#!/usr/bin/env python3
"""
PayPal → Banking Kalender — Version 3
Nur 8 Aktionen, ausschließlich bewährte Action-Identifier:
setvariable, matchtext, getitemfromlist, addnewevent
Titel/Notizen direkt inline im addnewevent (kein gettext mehr)
"""
import plistlib, uuid

def uid(): return str(uuid.uuid4()).upper()

U    = "￼"   # U+FFFC – Shortcut-Variablen-Platzhalter
DASH = "–"   # En-Dash

AM_UUID   = uid()
AM_I_UUID = uid()
ME_UUID   = uid()
ME_I_UUID = uid()

def var(name):
    return {"Value": {"Type": "Variable", "VariableName": name},
            "WFSerializationType": "WFTextTokenAttachment"}

def out(label, u):
    return {"Value": {"Type": "ActionOutput", "OutputName": label, "OutputUUID": u},
            "WFSerializationType": "WFTextTokenAttachment"}

def tok(s, r):
    return {"Value": {"string": s, "attachmentsByRange": r},
            "WFSerializationType": "WFTextTokenString"}

# ─── Titel: "PayPal – {Haendler} – {Betrag}" ─────────────────────────────────
# P(0)a(1)y(2)P(3)a(4)l(5) (6)–(7) (8)▯(9) (10)–(11) (12)▯(13)
title = tok(
    f"PayPal {DASH} {U} {DASH} {U}",
    {
        "{9, 1}":  {"Type": "Variable", "VariableName": "Haendler"},
        "{13, 1}": {"Type": "Variable", "VariableName": "Betrag"},
    }
)

# ─── Notizen ─────────────────────────────────────────────────────────────────
# "PayPal Zahlung\nBetrag: ▯\nHändler: ▯"
# P…g(13)\n(14)B…:(21) (22)▯(23)\n(24)H(25)ä(26)n(27)d(28)l(29)e(30)r(31):(32) (33)▯(34)
notes = tok(
    f"PayPal Zahlung\nBetrag: {U}\nHändler: {U}",
    {
        "{23, 1}": {"Type": "Variable", "VariableName": "Betrag"},
        "{34, 1}": {"Type": "Variable", "VariableName": "Haendler"},
    }
)

actions = [
    # 1. Mail-Eingabe als Variable speichern (Shortcut-Input = die E-Mail)
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "MailMsg"
            # kein WFInput → Shortcut-Input (die Mail) wird genommen
        }
    },

    # 2. Betrag suchen: "29,99 EUR" / "29,99€"
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.matchtext",
        "WFWorkflowActionParameters": {
            "UUID": AM_UUID,
            "WFMatchTextPattern": r"\d[\d.]*[.,]\d{2}\s*(?:EUR|€)",
            "WFMatchTextCaseSensitive": False,
            "WFInput": var("MailMsg")
        }
    },

    # 3. Ersten Betrag-Treffer nehmen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
        "WFWorkflowActionParameters": {
            "UUID": AM_I_UUID,
            "WFItemSpecifier": "First Item",
            "WFInput": out("Matches", AM_UUID)
        }
    },

    # 4. Variable "Betrag" setzen
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

    # 6. Ersten Händler-Treffer nehmen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
        "WFWorkflowActionParameters": {
            "UUID": ME_I_UUID,
            "WFItemSpecifier": "First Item",
            "WFInput": out("Matches", ME_UUID)
        }
    },

    # 7. Variable "Haendler" setzen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "Haendler",
            "WFInput": out("Item from List", ME_I_UUID)
        }
    },

    # 8. Kalender-Eintrag in "Banking" mit Titel+Notizen direkt inline
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.addnewevent",
        "WFWorkflowActionParameters": {
            "WFCalendarItemTitle": title,
            "WFCalendarItemCalendar": "Banking",
            "WFCalendarItemAllDay": True,
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
