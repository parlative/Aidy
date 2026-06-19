#!/usr/bin/env python3
"""
Generates Apple Shortcuts .shortcut file:
PayPal-E-Mail → Kalender-Eintrag im "Banking"-Kalender

Trigger: Share Sheet in Apple Mail
Extracts: Betrag (z.B. "29,99 EUR"), Händler
Creates: Kalender-Eintrag in "Banking"
"""
import plistlib
import uuid

def uid():
    return str(uuid.uuid4()).upper()

U = "￼"   # U+FFFC — Object Replacement Character (Shortcut variable placeholder)
DASH = "–"  # En-Dash

# UUIDs für Action-Outputs
SUBJ_UUID      = uid()
BODY_UUID      = uid()
AM_MATCH_UUID  = uid()
AM_ITEM_UUID   = uid()
ME_MATCH_UUID  = uid()
ME_ITEM_UUID   = uid()
TITLE_UUID     = uid()
NOTES_UUID     = uid()
RESULT_UUID    = uid()

def var_in(name):
    return {
        "Value": {"Type": "Variable", "VariableName": name},
        "WFSerializationType": "WFTextTokenAttachment"
    }

def act_out(output_name, output_uuid):
    return {
        "Value": {"Type": "ActionOutput", "OutputName": output_name, "OutputUUID": output_uuid},
        "WFSerializationType": "WFTextTokenAttachment"
    }

def tok(s, ranges):
    """WFTextTokenString mit eingebetteten Variablen"""
    return {
        "Value": {"string": s, "attachmentsByRange": ranges},
        "WFSerializationType": "WFTextTokenString"
    }

# ─── Kalender-Titel ───────────────────────────────────────────────────────────
# "PayPal – {Haendler} – {Betrag}"
#  P(0)a(1)y(2)P(3)a(4)l(5) (6)–(7) (8)▯(9) (10)–(11) (12)▯(13)
title_str = f"PayPal {DASH} {U} {DASH} {U}"
title_ranges = {
    "{9, 1}":  {"Type": "Variable", "VariableName": "Haendler"},
    "{13, 1}": {"Type": "Variable", "VariableName": "Betrag"},
}

# ─── Notizen ─────────────────────────────────────────────────────────────────
# "PayPal Zahlung\nBetrag: ▯\nHändler: ▯\nBetreff: ▯"
# P(0)…g(13)\n(14)B(15)…g(20):(21) (22)▯(23)\n(24)H(25)ä(26)n(27)d(28)l(29)e(30)r(31):(32) (33)▯(34)\n(35)B(36)…f(42):(43) (44)▯(45)
notes_str = f"PayPal Zahlung\nBetrag: {U}\nHändler: {U}\nBetreff: {U}"
notes_ranges = {
    "{23, 1}": {"Type": "Variable", "VariableName": "Betrag"},
    "{34, 1}": {"Type": "Variable", "VariableName": "Haendler"},
    "{45, 1}": {"Type": "Variable", "VariableName": "Betreff"},
}

# ─── Ergebnis-Text ───────────────────────────────────────────────────────────
# "✅ Banking-Eintrag gespeichert:\n▯ – ▯"
# ✅(0) (1)B(2)…g(8)-(9)E(10)…g(17) (18)g(19)…t(28):(29)\n(30)▯(31) (32)–(33) (34)▯(35)
result_str = f"✅ Banking-Eintrag gespeichert:\n{U} {DASH} {U}"
result_ranges = {
    "{31, 1}": {"Type": "Variable", "VariableName": "Haendler"},
    "{35, 1}": {"Type": "Variable", "VariableName": "Betrag"},
}

actions = [
    # 1. E-Mail-Variable speichern (Shortcut-Input = die Mail)
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {"WFVariableName": "PayPalEmail"}
        # WFInput nicht angegeben → verwendet Shortcut-Input (die Mail)
    },

    # 2. Betreff holen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getmailmessagecontent",
        "WFWorkflowActionParameters": {
            "UUID": SUBJ_UUID,
            "WFGetMailMessageContentField": "Subject",
            "WFInput": var_in("PayPalEmail")
        }
    },

    # 3. Variable "Betreff" setzen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "Betreff",
            "WFInput": act_out("Contents of Mail Message", SUBJ_UUID)
        }
    },

    # 4. E-Mail-Body holen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getmailmessagecontent",
        "WFWorkflowActionParameters": {
            "UUID": BODY_UUID,
            "WFGetMailMessageContentField": "Body",
            "WFInput": var_in("PayPalEmail")
        }
    },

    # 5. Variable "EmailBody" setzen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "EmailBody",
            "WFInput": act_out("Contents of Mail Message", BODY_UUID)
        }
    },

    # 6. Betrag extrahieren: z.B. "29,99 EUR" oder "29,99 €"
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.matchtext",
        "WFWorkflowActionParameters": {
            "UUID": AM_MATCH_UUID,
            "WFMatchTextPattern": r"\d[\d.]*[.,]\d{2}\s*(?:EUR|€)",
            "WFMatchTextCaseSensitive": False,
            "WFInput": var_in("EmailBody")
        }
    },

    # 7. Ersten Betrag nehmen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
        "WFWorkflowActionParameters": {
            "UUID": AM_ITEM_UUID,
            "WFItemSpecifier": "First Item",
            "WFInput": act_out("Matches", AM_MATCH_UUID)
        }
    },

    # 8. Variable "Betrag" setzen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "Betrag",
            "WFInput": act_out("Item from List", AM_ITEM_UUID)
        }
    },

    # 9. Händler-Name extrahieren (Lookbehind "an ", vor "gesendet/bezahlt/genehmigt")
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.matchtext",
        "WFWorkflowActionParameters": {
            "UUID": ME_MATCH_UUID,
            "WFMatchTextPattern": r"(?<=\ban )([^\n\r]+?)(?= gesendet| bezahlt| genehmigt|\n|\r|$)",
            "WFMatchTextCaseSensitive": False,
            "WFInput": var_in("EmailBody")
        }
    },

    # 10. Ersten Händler-Treffer nehmen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
        "WFWorkflowActionParameters": {
            "UUID": ME_ITEM_UUID,
            "WFItemSpecifier": "First Item",
            "WFInput": act_out("Matches", ME_MATCH_UUID)
        }
    },

    # 11. Variable "Haendler" setzen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "Haendler",
            "WFInput": act_out("Item from List", ME_ITEM_UUID)
        }
    },

    # 12. Titel-Text bauen: "PayPal – Haendler – Betrag"
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "UUID": TITLE_UUID,
            "WFTextActionText": tok(title_str, title_ranges)
        }
    },

    # 13. Notizen-Text bauen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "UUID": NOTES_UUID,
            "WFTextActionText": tok(notes_str, notes_ranges)
        }
    },

    # 14. Kalender-Eintrag erstellen in "Banking", ganztägig, heute
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.addnewevent",
        "WFWorkflowActionParameters": {
            "WFCalendarItemTitle": act_out("Text", TITLE_UUID),
            "WFCalendarItemCalendar": "Banking",
            "WFCalendarItemAllDay": True,
            "WFCalendarItemNotes": act_out("Text", NOTES_UUID),
        }
    },

    # 15. Ergebnis anzeigen
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.showresult",
        "WFWorkflowActionParameters": {
            "UUID": RESULT_UUID,
            "Text": tok(result_str, result_ranges)
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
        "WFWorkflowIconStartColor": 946986751,   # Blau
        "WFWorkflowIconGlyphNumber": 59503        # Kalender-Symbol
    },
    "WFWorkflowActions": actions
}

out = "/home/user/Aidy/PayPal_Banking_Kalender.shortcut"
with open(out, "wb") as f:
    plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)

print(f"OK: {out}")

# Kurze Plausibilitätsprüfung
import os
size = os.path.getsize(out)
print(f"Dateigröße: {size} Bytes")
print(f"Anzahl Aktionen: {len(actions)}")
