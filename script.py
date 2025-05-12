import os
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A5
from reportlab.lib.utils import ImageReader
from io import BytesIO
from PIL import Image
import fitz  # PyMuPDF

# === PARAMÈTRES GLOBAUX =======================================================
COMPRESSION_QUALITE = 90  # Compression JPEG entre 1 (forte) et 100 (aucune)
NOM_PAGE_GARDE = "page_garde.pdf"
FICHIER_FINAL = "fichier_fusionne_A5.pdf"
DOSSIER_PARTITIONS = os.path.join(os.getcwd(), "partitions")
A5_LANDSCAPE = landscape(A5)
A5_WIDTH, A5_HEIGHT = A5_LANDSCAPE

# === SUPPRIMER LE FICHIER FINAL S’IL EXISTE ===================================
if os.path.exists(FICHIER_FINAL):
    os.remove(FICHIER_FINAL)

# === CHARGER LES PARTITIONS À JOUE ============================================
bdd = pd.read_csv("liste.csv")
musiques = bdd[bdd["JOUE"] == 1]

noms_fichiers = []
for _, row in musiques.iterrows():
    base = row["NOM_FICHIER"]
    base = f"{base}.pdf" if not base.endswith(".pdf") else base
    if row["NBR_VERSIONS"] > 1:
        noms_fichiers.extend([
            f"{base[:-4]}-{i}.pdf" for i in range(1, int(row["NBR_VERSIONS"]) + 1)
        ])
    else:
        noms_fichiers.append(base)

pdfs_a_traiter = [NOM_PAGE_GARDE] + [
    os.path.join(DOSSIER_PARTITIONS, nom)
    for nom in noms_fichiers if os.path.exists(os.path.join(DOSSIER_PARTITIONS, nom))
]

# === CONVERSION DES PAGES EN A5 PAYSAGE AVEC COMPRESSION ======================


def convertir_page_dans_A5_paysage_compressé(pdf_path):
    doc = fitz.open(pdf_path)
    writer = PdfWriter()

    for page in doc:
        # Convertir en image (PixMap → PIL)
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Compresser l’image avec PIL
        img_buffer = BytesIO()
        img.save(img_buffer, format="JPEG", quality=COMPRESSION_QUALITE)
        img_buffer.seek(0)

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A5_LANDSCAPE)

        # Taille image compressée
        img = Image.open(img_buffer)
        img_width_pts = img.width * 72 / 300
        img_height_pts = img.height * 72 / 300

        # Adapter à A5 paysage (sans déformer)
        scale = min(A5_WIDTH / img_width_pts, A5_HEIGHT / img_height_pts, 1.0)
        new_width = img_width_pts * scale
        new_height = img_height_pts * scale

        dx = (A5_WIDTH - new_width) / 2
        dy = (A5_HEIGHT - new_height) / 2

        img_reader = ImageReader(img_buffer)
        c.drawImage(img_reader, dx, dy, width=new_width, height=new_height)
        c.showPage()
        c.save()

        buffer.seek(0)
        page_pdf = PdfReader(buffer)
        writer.add_page(page_pdf.pages[0])

    out = BytesIO()
    writer.write(out)
    out.seek(0)
    return out


# === FUSION DES PAGES ========================================================
merger = PdfMerger()

for pdf_path in pdfs_a_traiter:
    pdf_converti = convertir_page_dans_A5_paysage_compressé(pdf_path)
    merger.append(PdfReader(pdf_converti))

# === ÉCRITURE DU FICHIER FINAL ===============================================
merger.write(FICHIER_FINAL)
merger.close()

print(
    f"✅ PDF final généré et compressé à {COMPRESSION_QUALITE}% : {FICHIER_FINAL}")
