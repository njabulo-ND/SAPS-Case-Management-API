import base64
import io

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Image,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.platypus import Flowable
from reportlab.lib.utils import ImageReader


class RoundedBox(Flowable):
    def __init__(self, width, height, text="", radius=6):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.text = text or ""
        self.radius = radius

    def draw(self):
        canvas = self.canv
                # If the value is a Base64 image, draw the actual image
        if isinstance(self.text, str) and self.text.startswith("data:image"):
            base64_data = self.text.split(",", 1)[1]
            image_data = base64.b64decode(base64_data)

            signature = ImageReader(io.BytesIO(image_data))

            canvas.drawImage(
                signature,
                6,
                4,
                width=self.width - 12,
                height=self.height - 8,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto"
            )

            return

        # Rounded border
        canvas.roundRect(
            0,
            0,
            self.width,
            self.height,
            self.radius,
            stroke=1,
            fill=0
        )

        # Text that wraps inside the rounded box
        text_style = ParagraphStyle(
            "RoundedBoxText",
            fontName="Helvetica",
            fontSize=9,
            leading=11
        )

        paragraph = Paragraph(self.text, text_style)

        available_width = self.width - 12
        available_height = self.height - 10

        paragraph.wrap(
            available_width,
            available_height
        )

        paragraph.drawOn(
            canvas,
            6,
            self.height - paragraph.height - 6
        )
#Generating a pdf
def create_p21_layout(p21, styles, badge_path=None):
    elements = []

    # SAPS badge at the top
    if badge_path:
        badge = Image(badge_path, width=28 * mm, height=28 * mm)
        badge.hAlign = "CENTER"
        elements.append(badge)
        elements.append(Spacer(1, 4))

    # P21 heading
        heading = Table([
        [
            Paragraph("<b>G.P.S 0/02</b>", styles["Normal"]),
            Paragraph("<b>P.21</b>", styles["Title"])
        ]
    ], colWidths=[130 * mm, 35 * mm])

    heading.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(heading)
    elements.append(Spacer(1, 8))

       # I AM
    elements.append(Paragraph("<b>I AM</b>", styles["Normal"]))

    iam_box = RoundedBox(
        165 * mm,
        14 * mm,
        p21.get("iAm", "")
    )

    elements.append(iam_box)
    elements.append(Spacer(1, 10))
       # Language
    elements.append(
        Paragraph("<b>Language</b>", styles["Normal"])
    )

    language_box = RoundedBox(
        165 * mm,
        14 * mm,
        p21.get("lang", "")
    )

    elements.append(language_box)
    elements.append(Spacer(1, 12))

    # Statement section
        # Statement
    elements.append(
        Paragraph("<b>STATEMENT</b>", styles["Normal"])
    )

    statement_text = str(p21.get("statement") or "")

    # Dynamic height based on the amount of statement text
    characters_per_line = 100

    estimated_lines = max(
        1,
        (len(statement_text) + characters_per_line - 1)
        // characters_per_line
    )

    statement_height = max(
        90 * mm,
        (estimated_lines * 11) + 18
    )

    statement_box = RoundedBox(
        165 * mm,
        statement_height,
        statement_text
    )

    elements.append(statement_box)
    elements.append(Spacer(1, 12))
    # Declaration
    elements.append(
        Paragraph(
            "<b>I KNOW AND UNDERSTAND THE CONTENT OF THE ABOVE STATEMENT.</b>",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 18))

    elements.append(
        Paragraph(
            "<b>I CONSIDER THE ABOVE STATEMENT TO BE TRUTHFUL ON MY CONSENT.</b>",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 6))

    # Signature / Initials
      
    elements.append(
        Paragraph("<b>Signature / Initials</b>", styles["Normal"])
    )

    signature_value = p21.get("signature") or p21.get("initials") or ""

    signature_box = RoundedBox(
        165 * mm,
        16 * mm,
        signature_value
    )

    elements.append(signature_box)
    elements.append(Spacer(1, 18))

    # Footer divider
    footer_line = Table(
        [[""]],
        colWidths=[165 * mm],
        rowHeights=[1]
    )

    footer_line.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, -1), 0.8, colors.grey),
    ]))

    elements.append(footer_line)
    elements.append(Spacer(1, 8))

    # Footer information
    footer = Table([
        [
            Paragraph("Revision 1.0 Dated 2006-10-24", styles["Normal"]),
            Paragraph("Page 1", styles["Normal"])
        ]
    ], colWidths=[130 * mm, 35 * mm])

    footer.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(footer)

    return elements

def create_investigation_diary_layout(diary, styles):
    elements = []

        # SAPS badge
    badge = Image(
        "SAPS BADGE.jpeg",
        width=28 * mm,
        height=28 * mm
    )
    badge.hAlign = "CENTER"

    elements.append(badge)
    elements.append(Spacer(1, 4))

    # Main heading
       # Main heading
    elements.append(
        Paragraph("<b>INVESTIGATION DIARY</b>", styles["Title"])
    )
    elements.append(
        Paragraph("Case Investigation Log", styles["Normal"])
    )
    elements.append(Spacer(1, 14))

    # Case Information heading
    elements.append(
        Paragraph("<b>CASE INFORMATION</b>", styles["Heading2"])
    )

    divider = Table([[""]], colWidths=[165 * mm], rowHeights=[1 * mm])
    divider.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.8, colors.black)
    ]))

    elements.append(divider)
    elements.append(Spacer(1, 8))

    # Station and CAS number - rounded boxes
    station_box = RoundedBox(
        78 * mm,
        14 * mm,
        diary.get("station") or ""
    )

    cas_box = RoundedBox(
        78 * mm,
        14 * mm,
        diary.get("caseNumber") or ""
    )

    case_info = Table([
        [
            Paragraph("<b>STATION</b>", styles["Normal"]),
            Paragraph("<b>CAS NO.</b>", styles["Normal"])
        ],
        [
            station_box,
            cas_box
        ]
    ], colWidths=[82.5 * mm, 82.5 * mm])

    case_info.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    elements.append(case_info)
    elements.append(Spacer(1, 14))
    # Investigation Entries
        # Investigation Entries
    elements.append(
        Paragraph("<b>INVESTIGATION ENTRIES</b>", styles["Heading2"])
    )

    entry_divider = Table([[""]], colWidths=[165 * mm], rowHeights=[1 * mm])
    entry_divider.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.8, colors.black)
    ]))

    elements.append(entry_divider)
    elements.append(Spacer(1, 8))

    for entry in diary.get("entries", []):
        date_box = RoundedBox(
            48 * mm,
            14 * mm,
            entry.get("date") or ""
        )

        time_box = RoundedBox(
            48 * mm,
            14 * mm,
            entry.get("time") or ""
        )

        particulars_text = str(entry.get("particulars") or "")

        # Increase the box height depending on the amount of text
        characters_per_line = 70
        estimated_lines = max(
            1,
            (len(particulars_text) + characters_per_line - 1) // characters_per_line
        )

        particulars_height = max(
            35 * mm,
            (estimated_lines * 11) + 14
        )

        particulars_box = RoundedBox(
            108 * mm,
            particulars_height,
            particulars_text
        )

        entry_layout = Table([
            [
                Paragraph("<b>DATE</b>", styles["Normal"]),
                "",
                Paragraph("<b>PARTICULARS OF INVESTIGATION</b>", styles["Normal"])
            ],
            [
                date_box,
                "",
                particulars_box
            ],
            [
                Paragraph("<b>TIME</b>", styles["Normal"]),
                "",
                ""
            ],
            [
                time_box,
                "",
                ""
            ]
        ], colWidths=[50 * mm, 7 * mm, 108 * mm])

        entry_layout.setStyle(TableStyle([
            ("SPAN", (2, 1), (2, 3)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

        elements.append(entry_layout)
        elements.append(Spacer(1, 10))

    # Additional Notes
        # Additional Notes
    elements.append(Spacer(1, 8))

    elements.append(
        Paragraph("<b>ADDITIONAL NOTES</b>", styles["Heading2"])
    )

    notes_divider = Table([[""]], colWidths=[165 * mm], rowHeights=[1 * mm])
    notes_divider.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.8, colors.black)
    ]))

    elements.append(notes_divider)
    elements.append(Spacer(1, 8))

    notes_text = str(diary.get("notes") or "")

    characters_per_line = 100
    estimated_lines = max(
        1,
        (len(notes_text) + characters_per_line - 1) // characters_per_line
    )

    notes_height = max(
        28 * mm,
        (estimated_lines * 11) + 14
    )

    notes_box = RoundedBox(
        165 * mm,
        notes_height,
        notes_text
    )

    elements.append(notes_box)
    # Investigating Officer
       
    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph("<b>INVESTIGATING OFFICER</b>", styles["Heading2"])
    )

    officer_divider = Table([[""]], colWidths=[165 * mm], rowHeights=[1 * mm])
    officer_divider.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.8, colors.black)
    ]))

    elements.append(officer_divider)
    elements.append(Spacer(1, 8))

    officer_text = str(diary.get("investigatingOfficer") or "")

    officer_box = RoundedBox(
        165 * mm,
        16 * mm,
        officer_text
    )

    elements.append(officer_box)
    elements.append(Spacer(1, 14))

   

    return elements

def create_modus_operandi_layout(modus, styles):
    elements = []

    # SAPS badge
    badge = Image(
        "SAPS BADGE.jpeg",
        width=28 * mm,
        height=28 * mm
    )
    badge.hAlign = "CENTER"

    elements.append(badge)
    elements.append(Spacer(1, 4))

    # Main heading
    elements.append(
        Paragraph("<b>MODUS OPERANDI</b>", styles["Title"])
    )
    elements.append(Spacer(1, 12))

    # Case information
    case_info = Table([
        [
            Paragraph("<b>CASE NUMBER</b>", styles["Normal"]),
            Paragraph(str(modus.get("caseNumber") or ""), styles["Normal"])
        ],
        [
            Paragraph("<b>IR</b>", styles["Normal"]),
            Paragraph(str(modus.get("ir") or ""), styles["Normal"])
        ]
    ], colWidths=[45 * mm, 120 * mm])

    case_info.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elements.append(case_info)
    elements.append(Spacer(1, 14))

    # Main Modus Operandi details
    details = [
        ("A. OFFENCE", modus.get("A_offence", "")),
        ("B. DATE", modus.get("B_date", "")),
        ("C. TIME", modus.get("C_time", "")),
        ("D. PLACE", modus.get("D_place", "")),
        ("E. METHOD USED", modus.get("E_methodUsed", "")),
        ("F. INSTRUMENT USED", modus.get("F_instrumentUsed", "")),
        ("G. PROPERTY INVOLVED AND VALUE",
         modus.get("G_propertyInvolvedAndValue", "")),
        ("H. SERIAL / REGISTRATION NO.",
         modus.get("H_serialOrRegistrationNo", ""))
    ]

    detail_rows = []

    for label, value in details:
        detail_rows.append([
            Paragraph(f"<b>{label}</b>", styles["Normal"]),
            Paragraph(str(value or ""), styles["Normal"])
        ])

    details_table = Table(
        detail_rows,
        colWidths=[55 * mm, 110 * mm]
    )

    details_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elements.append(details_table)
    elements.append(Spacer(1, 14))

    # I. Suspects
    elements.append(
        Paragraph("<b>I. SUSPECTS</b>", styles["Heading2"])
    )
    elements.append(Spacer(1, 6))

    suspect_rows = [[
        Paragraph("<b>INVOLVED</b>", styles["Normal"]),
        Paragraph("<b>DESCRIPTION</b>", styles["Normal"])
    ]]

    for suspect in modus.get("I_suspects", []):
        suspect_rows.append([
            Paragraph(
                str(suspect.get("involved", "")),
                styles["Normal"]
            ),
            Paragraph(
                str(suspect.get("description", "")),
                styles["Normal"]
            )
        ])

    suspects_table = Table(
        suspect_rows,
        colWidths=[50 * mm, 115 * mm]
    )

    suspects_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elements.append(suspects_table)
    elements.append(Spacer(1, 14))

    # J - M Details
    remaining_details = [
        ("J. WITNESS DETAILS", modus.get("J_witnessDetails", "")),
        ("K. CIRCULATION NO.", modus.get("K_circulationNo", "")),
        ("K. LCRC NO.", modus.get("K_lcrcNo", "")),
        ("L. SAP 13 NO.", modus.get("L_sap13No", "")),
        ("L. SAP 14 NO.", modus.get("L_sap14No", "")),
        ("M. COMMENTS", modus.get("M_comments", ""))
    ]

    remaining_rows = []

    for label, value in remaining_details:
        remaining_rows.append([
            Paragraph(f"<b>{label}</b>", styles["Normal"]),
            Paragraph(str(value or ""), styles["Normal"])
        ])

    remaining_table = Table(
        remaining_rows,
        colWidths=[55 * mm, 110 * mm]
    )

    remaining_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elements.append(remaining_table)
    elements.append(Spacer(1, 14))

    # N. Compiled By and O. Perused By
    compiled = modus.get("N_compiledBy", {})
    perused = modus.get("O_perusedBy", {})

    officer_rows = [
        [
            Paragraph("<b>N. COMPILED BY</b>", styles["Normal"]),
            Paragraph("<b>O. PERUSED BY</b>", styles["Normal"])
        ],
        [
            Paragraph(
                f"<b>No:</b> {compiled.get('no') or ''}<br/>"
                f"<b>Rank:</b> {compiled.get('rank') or ''}<br/>"
                f"<b>Initial & Surname:</b> {compiled.get('initialAndSurname') or ''}",
                styles["Normal"]
            ),
            Paragraph(
                f"<b>No:</b> {perused.get('no') or ''}<br/>"
                f"<b>Rank:</b> {perused.get('rank') or ''}<br/>"
                f"<b>Initial & Signature:</b> {perused.get('initialAndSignature') or ''}",
                styles["Normal"]
            )
        ]
    ]

    officer_table = Table(
        officer_rows,
        colWidths=[82.5 * mm, 82.5 * mm]
    )

    officer_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(officer_table)

    return elements

def create_statement_form_layout(statement, styles):
    elements = []

    # SAPS badge
    badge = Image(
        "SAPS BADGE.jpeg",
        width=28 * mm,
        height=28 * mm
    )
    badge.hAlign = "CENTER"

    elements.append(badge)
    elements.append(Spacer(1, 4))

    # Main heading
    elements.append(
        Paragraph("<b>STATEMENT FORM</b>", styles["Title"])
    )
    elements.append(Spacer(1, 12))

    # Station and case number
    case_info = Table([
        [
            Paragraph("<b>STATION</b>", styles["Normal"]),
            Paragraph(str(statement.get("station") or ""), styles["Normal"])
        ],
        [
            Paragraph("<b>CASE NUMBER</b>", styles["Normal"]),
            Paragraph(str(statement.get("caseNumber") or ""), styles["Normal"])
        ]
    ], colWidths=[45 * mm, 120 * mm])

    case_info.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elements.append(case_info)
    elements.append(Spacer(1, 14))

    # Date and time when the incident occurred
    when_certain = statement.get("whenCertain", {})

    elements.append(
        Paragraph("<b>DATE AND TIME OF INCIDENT</b>", styles["Heading2"])
    )
    elements.append(Spacer(1, 6))

    date_time_table = Table([
        [
            Paragraph(
                str(when_certain.get("description") or ""),
                styles["Normal"]
            )
        ],
        [
            Paragraph("<b>DATE</b>", styles["Normal"]),
            Paragraph(str(when_certain.get("date") or ""), styles["Normal"]),
            Paragraph("<b>TIME</b>", styles["Normal"]),
            Paragraph(str(when_certain.get("time") or ""), styles["Normal"])
        ]
    ], colWidths=[35 * mm, 50 * mm, 30 * mm, 50 * mm])

    date_time_table.setStyle(TableStyle([
        ("SPAN", (0, 0), (3, 0)),
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elements.append(date_time_table)
    elements.append(Spacer(1, 12))

    # Approximate date/time range
    uncertain = statement.get("whenUncertainRange", {})
    from_data = uncertain.get("from", {})
    to_data = uncertain.get("to", {})

    uncertain_rows = [
        [
            Paragraph(
                str(uncertain.get("description") or ""),
                styles["Normal"]
            )
        ],
        [
            Paragraph("<b>FROM DATE</b>", styles["Normal"]),
            Paragraph(str(from_data.get("date") or ""), styles["Normal"]),
            Paragraph("<b>FROM TIME</b>", styles["Normal"]),
            Paragraph(str(from_data.get("time") or ""), styles["Normal"])
        ],
        [
            Paragraph("<b>TO DATE</b>", styles["Normal"]),
            Paragraph(str(to_data.get("date") or ""), styles["Normal"]),
            Paragraph("<b>TO TIME</b>", styles["Normal"]),
            Paragraph(str(to_data.get("time") or ""), styles["Normal"])
        ]
    ]

    uncertain_table = Table(
        uncertain_rows,
        colWidths=[35 * mm, 50 * mm, 30 * mm, 50 * mm]
    )

    uncertain_table.setStyle(TableStyle([
        ("SPAN", (0, 0), (3, 0)),
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elements.append(uncertain_table)
    elements.append(Spacer(1, 12))

    # Day of week and offence
    day_offence_table = Table([
        [
            Paragraph("<b>DAY OF WEEK</b>", styles["Normal"]),
            Paragraph(str(statement.get("dayOfWeek") or ""), styles["Normal"])
        ],
        [
            Paragraph("<b>OFFENCE DESCRIPTION</b>", styles["Normal"]),
            Paragraph(str(statement.get("offenceDescription") or ""), styles["Normal"])
        ]
    ], colWidths=[55 * mm, 110 * mm])

    day_offence_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elements.append(day_offence_table)
    elements.append(Spacer(1, 12))

    # Method of entrance and instrument used
    incident_details = Table([
        [
            Paragraph("<b>METHOD OF ENTRANCE</b>", styles["Normal"]),
            Paragraph(str(statement.get("methodEntrance") or ""), styles["Normal"])
        ],
        [
            Paragraph("<b>INSTRUMENT TYPE</b>", styles["Normal"]),
            Paragraph(str(statement.get("instrumentType") or ""), styles["Normal"])
        ]
    ], colWidths=[55 * mm, 110 * mm])

    incident_details.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elements.append(incident_details)
    elements.append(Spacer(1, 12))

    # Scene details
    scene = statement.get("scene", {})

    elements.append(
        Paragraph("<b>SCENE OF INCIDENT</b>", styles["Heading2"])
    )
    elements.append(Spacer(1, 6))

    scene_rows = [
        ("BETWEEN A", scene.get("betweenA", "")),
        ("BETWEEN B", scene.get("betweenB", "")),
        ("STREET", scene.get("street", "")),
        ("BUILDING", scene.get("building", "")),
        ("SUBURB", scene.get("suburb", "")),
        ("TOWN", scene.get("town", ""))
    ]

    scene_table_data = []

    for label, value in scene_rows:
        scene_table_data.append([
            Paragraph(f"<b>{label}</b>", styles["Normal"]),
            Paragraph(str(value or ""), styles["Normal"])
        ])

    scene_table = Table(
        scene_table_data,
        colWidths=[55 * mm, 110 * mm]
    )

    scene_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elements.append(scene_table)
    elements.append(Spacer(1, 12))

    # Additional location details
    location_details = [
        ("POSTAL CODE", statement.get("postalCode", "")),
        ("GEOGRAPHICAL BLOCK", statement.get("geographicalBlock", "")),
        ("PREMISES TYPE", statement.get("premisesType", ""))
    ]

    location_rows = []

    for label, value in location_details:
        location_rows.append([
            Paragraph(f"<b>{label}</b>", styles["Normal"]),
            Paragraph(str(value or ""), styles["Normal"])
        ])

    location_table = Table(
        location_rows,
        colWidths=[55 * mm, 110 * mm]
    )

    location_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elements.append(location_table)
    elements.append(Spacer(1, 14))

        # Final date and signature section
    signature_value = statement.get("signature") or ""

    signature_display = RoundedBox(
        105 * mm,
        18 * mm,
        signature_value
    )

    final_table = Table([
        [
            Paragraph("<b>DATE</b>", styles["Normal"]),
            Paragraph(
                str(statement.get("footerDate") or ""),
                styles["Normal"]
            )
        ],
        [
            Paragraph("<b>SIGNATURE</b>", styles["Normal"]),
            signature_display
        ]
    ], colWidths=[55 * mm, 110 * mm])

    final_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elements.append(final_table)
    return elements

def generate_case_pdf(forms, output_path="dictionary_case.pdf"):
    """
    Builds a combined PDF from a dictionary of forms.

    forms: dict of {form_name: form_data_dict}
    output_path: filename/path to save the PDF to

    Returns the output_path on success, or None on failure.
    """

    styles = getSampleStyleSheet()
    content = []

    def add_to_pdf(key, value):

        # NESTED DICTIONARY
        if isinstance(value, dict):

            content.append(
                Paragraph(f"<b>{key}</b>", styles["Heading3"])
            )

            for sub_key, sub_value in value.items():
                add_to_pdf(sub_key, sub_value)

        # LIST
        elif isinstance(value, list):

            content.append(
                Paragraph(f"<b>{key}</b>", styles["Heading3"])
            )

            for number, item in enumerate(value, start=1):

                content.append(
                    Paragraph(
                        f"<b>Item {number}</b>",
                        styles["Normal"]
                    )
                )

                if isinstance(item, dict):
                    for sub_key, sub_value in item.items():
                        add_to_pdf(sub_key, sub_value)
                else:
                    add_to_pdf("", item)

                content.append(Spacer(1, 8))

        # SIGNATURE IMAGE
        elif (
            key.lower() in ["signature", "initialandsignature"]
            and isinstance(value, str)
            and value.startswith("data:image")
        ):

            base64_data = value.split(",", 1)[1]
            image_data = base64.b64decode(base64_data)

            signature_image = Image(
                io.BytesIO(image_data),
                width=2 * inch,
                height=0.8 * inch
            )

            content.append(
                Paragraph(f"<b>{key}:</b>", styles["Normal"])
            )

            content.append(signature_image)
            content.append(Spacer(1, 8))

        # NORMAL VALUE
        else:

            display_value = value if value not in ["", None] else "Not specified"

            content.append(
                Paragraph(
                    f"<b>{key}:</b> {display_value}",
                    styles["Normal"]
                )
            )

            content.append(Spacer(1, 6))

    try:
        pdf = SimpleDocTemplate(output_path)

        # ITERATE THROUGH ALL FORMS
        for form_name, form_data in forms.items():

            if form_name == "P21":
                content.extend(
                    create_p21_layout(
                        form_data,
                        styles,
                        badge_path="SAPS BADGE.jpeg"
                    )
                )
                content.append(PageBreak())
                continue

            if form_name == "INVESTIGATION DIARY":
                content.extend(
                    create_investigation_diary_layout(
                        form_data,
                        styles
                    )
                )
    
                continue
            if form_name == "MODUS OPERANDI":
                content.extend(
                    create_modus_operandi_layout(
                        form_data,
                        styles
                    )
                )
                content.append(PageBreak())
                continue
            if form_name == "STATEMENT FORM":
                content.extend(
                    create_statement_form_layout(
                        form_data,
                        styles
                    )
                )
                content.append(PageBreak())
                continue
    

        def draw_footer(canvas, doc):
            if canvas.getPageNumber() == 2:
                canvas.saveState()

                canvas.setLineWidth(0.8)
                canvas.line(25 * mm, 18 * mm, 185 * mm, 18 * mm)

                canvas.setFont("Helvetica", 9)
                canvas.drawString(
                    25 * mm,
                    12 * mm,
                    "Revision 1.0 Dated 2006-10-24"
                )

                canvas.drawRightString(
                    185 * mm,
                    12 * mm,
                    "Page 2"
                )

                canvas.restoreState()

        pdf.build(
            content,
            onFirstPage=draw_footer,
            onLaterPages=draw_footer
        )

        print(f"Combined PDF created successfully at {output_path}!")
        return output_path

    except Exception as e:
        print(f"Failed to create PDF. Error: {e}")
        return None