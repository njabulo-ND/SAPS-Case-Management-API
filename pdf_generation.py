import base64
import io

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Image
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

#Generating a pdf
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

            content.append(
                Paragraph(form_name, styles["Title"])
            )

            content.append(Spacer(1, 15))

            for key, value in form_data.items():
                add_to_pdf(key, value)

            content.append(PageBreak())

        pdf.build(content)

        print(f"Combined PDF created successfully at {output_path}!")
        return output_path

    except Exception as e:
        print(f"Failed to create PDF. Error: {e}")
        return None