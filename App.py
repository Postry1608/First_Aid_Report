import base64
import datetime
from io import BytesIO
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import streamlit as st
from streamlit_drawable_canvas import st_canvas

# Force wide/mobile-friendly viewport
st.set_page_config(
    page_title="First Aid Report", layout="centered", initial_sidebar_state="collapsed"
)

# Custom CSS for bigger touch targets on mobile screens
st.markdown(
    """
    <style>
    .stButton button, .stLinkButton a {
        width: 100%;
        height: 3rem;
        font-size: 1.1rem;
        font-weight: bold;
    }
    textarea, input {
        font-size: 1rem !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("📋 FIRST AID REPORT")

# --- SECTION 1: INJURED PERSON DETAILS ---
st.subheader("1. Injured Person Details")
injured_name = st.text_input("Injured Person's Name")
age = st.text_input("Age (if under 18 yrs)")
address = st.text_area("Address", height=100)
postcode = st.text_input("Post Code")
phone = st.text_input("Phone Number")

st.markdown("**Wristband / iCard Scanning**")
card_number = st.text_input(
    "Wristband / iCard Number",
    key="card_num",
    placeholder="Tap button below to check/scan card...",
)
st.link_button(
    "📲 Scan Wristband / iCard", "https://semnox.404labs.co.uk/balance-checker"
)

st.divider()

# --- SECTION 2: INCIDENT DETAILS ---
st.subheader("2. Incident Details")
incident_date = st.date_input("Date of Incident", datetime.date.today())
incident_time = st.time_input(
    "Time of Incident", datetime.datetime.now().time()
)
location = st.text_input("Location of Incident")
statement = st.text_area("Statement of Account (What happened)", height=120)
injuries = st.text_area("Injuries Caused", height=100)
treatment = st.text_area("Treatment or Advice Given", height=100)

st.divider()

# --- SECTION 3: FIRST AIDER DETAILS ---
st.subheader("3. First Aider & Additional Info")
first_aider_name = st.text_input("First Aider Name")
department = st.text_input("Department")
additional_info = st.text_area("Additional Information", height=100)

st.divider()

# --- SECTION 4: SIGNATURES ---
st.subheader("4. Signatures")

st.write("✍️ **Injured Person Signature**")
canvas_injured = st_canvas(
    stroke_width=2,
    stroke_color="#000000",
    background_color="#F0F2F6",
    height=120,
    width=320,
    drawing_mode="freedraw",
    key="sig_injured",
)

st.write("✍️ **Sign here if Casualty REFUSED First Aid**")
canvas_refused = st_canvas(
    stroke_width=2,
    stroke_color="#000000",
    background_color="#F0F2F6",
    height=120,
    width=320,
    drawing_mode="freedraw",
    key="sig_refused",
)

st.write("✍️ **Sign here if Casualty WAS ADVISED to go to Hospital**")
canvas_hospital = st_canvas(
    stroke_width=2,
    stroke_color="#000000",
    background_color="#F0F2F6",
    height=120,
    width=320,
    drawing_mode="freedraw",
    key="sig_hospital",
)


# --- PDF GENERATION FUNCTION ---
def generate_pdf():
  buffer = BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=A4,
      rightMargin=20,
      leftMargin=20,
      topMargin=20,
      bottomMargin=20,
  )
  elements = []

  styles = getSampleStyleSheet()
  title_style = ParagraphStyle(
      "Title", parent=styles["Heading1"], alignment=1, fontSize=16, leading=20
  )
  bold_style = ParagraphStyle(
      "Bold", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9
  )
  normal_style = ParagraphStyle("Normal", parent=styles["Normal"], fontSize=9)

  elements.append(Paragraph("<b>FIRST AID REPORT</b>", title_style))
  elements.append(Spacer(1, 10))

  def make_cell(label, value):
    return Paragraph(f"<b>{label}:</b> {value or ''}", normal_style)

  # Main Info Table
  data_table1 = [
      [
          make_cell("INJURED PERSONS NAME", injured_name),
          make_cell("AGE (if under 18)", age),
      ],
      [
          make_cell("ADDRESS", address),
          make_cell("POST CODE", postcode),
      ],
      [
          make_cell("PHONE NUMBER", phone),
          make_cell("WRISTBAND/iCARD NO", card_number),
      ],
      [
          make_cell("DATE OF INCIDENT", str(incident_date)),
          make_cell("TIME OF INCIDENT", str(incident_time)),
      ],
      [make_cell("LOCATION OF INCIDENT", location), ""],
  ]
  t1 = Table(data_table1, colWidths=[350, 200])
  t1.setStyle(
      TableStyle([
          ("SPAN", (0, 4), (1, 4)),
          ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
      ])
  )
  elements.append(t1)
  elements.append(Spacer(1, 8))

  # Section Block Helper
  def add_block(header, content):
    data = [[
        Paragraph(f"<b>{header}</b>", bold_style)
    ], [
        Paragraph(content or "", normal_style)
    ]]
    t = Table(data, colWidths=[550])
    t.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (0, 0), colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
  elements.append(t)
  elements.append(Spacer(1, 8))

  add_block("INJURED PERSONS STATEMENT OF ACCOUNT", statement)
  add_block("ANY INJURIES CAUSED", injuries)
  add_block("TREATMENT OR ADVICE GIVEN", treatment)

  # Helper to process signatures
  def get_sig_image(canvas):
    if canvas.image_data is not None and canvas.image_data.any():
      img = Image.fromarray(canvas.image_data.astype("uint8"), "RGBA")
      img_byte_arr = BytesIO()
      img.save(img_byte_arr, format="PNG")
      img_byte_arr.seek(0)
      return RLImage(img_byte_arr, width=140, height=45)
    return Paragraph("<i>No Signature Provided</i>", normal_style)

  # Signatures and First Aider Table
  data_sig = [
      [
          Paragraph("<b>INJURED PERSON SIGNATURE:</b>", bold_style),
          get_sig_image(canvas_injured),
      ],
      [
          make_cell("FIRST AIDER NAME", first_aider_name),
          make_cell("DEPARTMENT", department),
      ],
      [
          Paragraph("<b>REFUSED FIRST AID SIGNATURE:</b>", bold_style),
          get_sig_image(canvas_refused),
      ],
      [
          Paragraph("<b>ADVISED TO GO TO HOSPITAL SIGNATURE:</b>", bold_style),
          get_sig_image(canvas_hospital),
      ],
  ]
  t_sig = Table(data_sig, colWidths=[275, 275])
  t_sig.setStyle(
      TableStyle([
          ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
      ])
  )
  elements.append(t_sig)
  elements.append(Spacer(1, 8))

  add_block("ADDITIONAL INFORMATION RELEVANT TO THE REPORT", additional_info)

  doc.build(elements)
  buffer.seek(0)
  return buffer


# --- EXPORT / DOWNLOAD ---
st.divider()
if st.button("📄 Generate First Aid PDF Report"):
  pdf_data = generate_pdf()
  st.download_button(
      label="📥 Download PDF to Device",
      data=pdf_data,
      file_name=f"First_Aid_Report_{injured_name or 'Incident'}.pdf",
      mime="application/pdf",
  )
