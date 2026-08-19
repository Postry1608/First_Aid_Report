import io
import os
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="First Aid Reporter", layout="centered")

# --- HIDE "PRESS ENTER TO SUBMIT" & STEPPER (+/-) BUTTONS VIA CSS ---
st.markdown(
    """
    <style>
    div[data-testid="InputInstructions"] {
        display: none !important;
    }
    button[data-testid="stNumberInputStepDown"],
    button[data-testid="stNumberInputStepUp"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- APP HEADER & LOGO ---
if os.path.exists("logo.png"):
    st.image("logo.png", width=240)

st.title("📋 First Aid Incident Report")
st.warning(
    "⚠️ All text boxes require descriptive sentences. Vague one or two-word"
    " entries will block submission."
)


# --- DIALOG POP-UP FOR DOWNLOAD & REMINDER ---
@st.dialog("✅ Report Generated Successfully")
def show_download_dialog(pdf_bytes, file_name):
    st.success("The First Aid Report has been compiled and validated.")
    st.warning(
        "📧 **Action Required:**\n\n"
        "Please ensure a copy of this generated report is emailed to:\n\n"
        "👉 **Safety@fantasyislandresort.co.uk**"
    )
    st.download_button(
        label="📲 Download Validated Report PDF",
        data=pdf_bytes,
        file_name=file_name,
        mime="application/pdf",
        use_container_width=True,
    )


# --- INPUT FORM ---
with st.form("first_aid_form", clear_on_submit=False):
    st.subheader("1. Casualty & Incident Details")
    col1, col2 = st.columns(2)
    with col1:
        casualty_name = st.text_input("Injured Person's Name *")
        phone = st.text_input("Phone Number *")
        age = st.number_input(
            "Age (If under 18)", min_value=0, max_value=100, value=None, step=1
        )
    with col2:
        address = st.text_input("Address & Postcode *")
        inc_date = st.date_input("Date of Incident", format="DD/MM/YYYY")
        inc_time = st.time_input("Time of Incident")

    icard_type = st.radio(
        "Ticket Type",
        ["Wristband", "iCard"],
        horizontal=True,
    )
    icard_num = st.text_input("Wristband / iCard Number (Type N/A if none) *")

    st.link_button(
        "📲 Scan Wristband / iCard (Opens in New Tab)",
        "https://semnox.404labs.co.uk/balance-checker",
    )

    st.subheader("2. Incident Location")
    loc_detail = st.text_input(
        "Incident Location (e.g., Ride, Off Site,"
        "Market Unit) *"
    )

    st.subheader("3. Incident & Clinical Details")
    statement = st.text_area(
        "Injured Person's Statement / Account *",
        placeholder="Describe the exact mechanism of the incident. What caused the fall? Use their words where possible.",
    )
    injuries = st.text_area(
        "Injuries Observed & Reported *",
        placeholder="Detail visible signs (swelling, cuts) and symptoms reported (pain level, numbness).",
    )
    treatment = st.text_area(
        "Treatment Given or Advice Provided *",
        placeholder="Detail all actions taken, equipment used (e.g., sling), and specific advice given.",
    )

    st.subheader("4. Disposition & Sign-Off")
    disposition = st.radio("Casualty Disposition *", [
        "Returned to Park / Resumed Activity",
        "Left Site",
    ])

    st.markdown("---")
    st.write("**Refusals & Advice Checkboxes**")
    refused_fa = st.checkbox("Casualty Refused First Aid")
    advised_hospital = st.checkbox("Casualty Advised to attend Hospital")

    fa_name = st.text_input("First Aider Name *")
    fa_dept = st.text_input("First Aider Department *")

    st.markdown("---")
    st.write("✍️ **Injured Person (or Parent/Guardian) Signature**")
    canvas_injured = st_canvas(
        stroke_width=2,
        stroke_color="#000",
        background_color="#F0F2F6",
        height=120,
        width=340,
        drawing_mode="freedraw",
        key="sig_inj",
    )

    submit_button = st.form_submit_button(
        "Verify and Generate Document", type="primary"
    )

# --- FORM VALIDATION & PDF GENERATION ---
if submit_button:
    required_fields = {
        "Casualty Name": casualty_name,
        "Phone Number": phone,
        "Address": address,
        "Ticket/Wristband Info": icard_num,
        "Incident Location": loc_detail,
        "Injured Person's Statement": statement,
        "Injuries Observed": injuries,
        "Treatment Given": treatment,
        "First Aider Name": fa_name,
        "First Aider Department": fa_dept,
    }

    missing_fields = []
    lazy_fields = []

    for label, val in required_fields.items():
        stripped_val = str(val).strip() if val is not None else ""
        if not stripped_val:
            missing_fields.append(label)
        elif label in [
            "Injured Person's Statement",
            "Injuries Observed",
            "Treatment Given",
        ] and len(stripped_val.split()) < 3:
            lazy_fields.append(label)

    if missing_fields:
        st.error(
            "❌ Cannot generate PDF. The following mandatory fields are empty:"
            f" {', '.join(missing_fields)}"
        )
    elif lazy_fields:
        st.error(
            "❌ Quality Check Failed: The text boxes for"
            f" **{', '.join(lazy_fields)}** require a full descriptive sentence,"
            " not just one or two words."
        )
    else:

        def generate_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30,
            )
            story = []

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "TitleStyle",
                parent=styles["Heading1"],
                fontSize=15,
                spaceAfter=0,
                textColor=colors.HexColor("#1A365D"),
            )
            h2_style = ParagraphStyle(
                "H2Style",
                parent=styles["Heading2"],
                fontSize=11,
                spaceBefore=8,
                spaceAfter=4,
                textColor=colors.HexColor("#2B6CB0"),
            )
            body_style = ParagraphStyle(
                "BodyStyle", parent=styles["BodyText"], fontSize=9, leading=13
            )
            bold_body = ParagraphStyle(
                "BoldBody", parent=body_style, fontName="Helvetica-Bold"
            )

            # --- GUARANTEED LOGO INTEGRATION IN PDF HEADER ---
            if os.path.exists("logo.png"):
                logo_img = RLImage("logo.png", width=120, height=45)
                header_data = [[
                    Paragraph("<b>FIRST AID INCIDENT REPORT</b>", title_style),
                    logo_img,
                ]]
            else:
                header_data = [[
                    Paragraph("<b>FIRST AID INCIDENT REPORT</b>", title_style),
                    Paragraph("", body_style),
                ]]

            header_table = Table(header_data, colWidths=[360, 170])
            header_table.setStyle(
                TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ])
            )
            story.append(header_table)
            story.append(Spacer(1, 10))

            formatted_date = inc_date.strftime("%d/%m/%Y") if inc_date else "N/A"

            # Block 1
            admin_data = [
                [
                    Paragraph("<b>Casualty Name:</b>", body_style),
                    Paragraph(casualty_name, body_style),
                    Paragraph("<b>Date / Time:</b>", body_style),
                    Paragraph(f"{formatted_date} @ {inc_time}", body_style),
                ],
                [
                    Paragraph("<b>Address:</b>", body_style),
                    Paragraph(address, body_style),
                    Paragraph("<b>Age:</b>", body_style),
                    Paragraph(
                        str(age) if age is not None and age != "" else "N/A",
                        body_style,
                    ),
                ],
                [
                    Paragraph("<b>Phone:</b>", body_style),
                    Paragraph(phone, body_style),
                    Paragraph("<b>Ticket Info:</b>", body_style),
                    Paragraph(f"{icard_type}: {icard_num}", body_style),
                ],
            ]
            t1 = Table(admin_data, colWidths=[90, 175, 90, 175])
            t1.setStyle(
                TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                    ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ])
            )
            story.append(Paragraph("1. Administrative & Asset Details", h2_style))
            story.append(t1)

            # Block 2
            story.append(Paragraph("2. Incident Location", h2_style))
            t2 = Table(
                [
                    [
                        Paragraph("<b>Verified Location:</b>", body_style),
                        Paragraph(loc_detail, body_style),
                    ]
                ],
                colWidths=[100, 430],
            )
            t2.setStyle(
                TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ])
            )
            story.append(t2)

            # Block 3
            story.append(Paragraph("3. Incident & Clinical Details", h2_style))
            narrative_data = [
                [Paragraph("<b>Injured Person's Statement:</b>", bold_body)],
                [Paragraph(statement, body_style)],
                [Paragraph("<b>Injuries Observed & Reported:</b>", bold_body)],
                [Paragraph(injuries, body_style)],
                [Paragraph("<b>Treatment or Advice Given:</b>", bold_body)],
                [Paragraph(treatment, body_style)],
            ]
            t3 = Table(narrative_data, colWidths=[530])
            t3.setStyle(
                TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, 0), colors.whitesmoke),
                    ("BACKGROUND", (0, 2), (0, 2), colors.whitesmoke),
                    ("BACKGROUND", (0, 4), (0, 4), colors.whitesmoke),
                ])
            )
            story.append(t3)

            # Helper for signatures in PDF
            def get_sig_img(canvas):
                if canvas.image_data is not None and canvas.image_data.any():
                    img = Image.fromarray(canvas.image_data.astype("uint8"), "RGBA")
                    img_b = io.BytesIO()
                    img.save(img_b, format="PNG")
                    img_b.seek(0)
                    return RLImage(img_b, width=140, height=40)
                return Paragraph("<i>None</i>", body_style)

            # Block 4
            story.append(Paragraph("4. Disposition & Sign-Offs", h2_style))
            sign_data = [
                [
                    Paragraph("<b>Disposition:</b>", body_style),
                    Paragraph(disposition, body_style),
                ],
                [
                    Paragraph("<b>Refused First Aid:</b>", body_style),
                    Paragraph("YES" if refused_fa else "NO", body_style),
                ],
                [
                    Paragraph("<b>Advised Hospital:</b>", body_style),
                    Paragraph("YES" if advised_hospital else "NO", body_style),
                ],
                [
                    Paragraph("<b>First Aider:</b>", body_style),
                    Paragraph(f"{fa_name} ({fa_dept})", body_style),
                ],
                [
                    Paragraph("<b>Casualty / Guardian Signature:</b>", body_style),
                    get_sig_img(canvas_injured),
                ],
            ]
            t4 = Table(sign_data, colWidths=[150, 380])
            t4.setStyle(
                TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ])
            )
            story.append(t4)

            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()

        pdf_bytes = generate_pdf()
        file_name = f"First_Aid_{casualty_name.replace(' ', '_')}_{inc_date.strftime('%d-%m-%Y')}.pdf"

        show_download_dialog(pdf_bytes, file_name)
