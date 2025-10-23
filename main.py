import os
import pandas as pd
import s3fs
import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A5
from reportlab.lib.utils import ImageReader
from io import BytesIO
from PIL import Image

# --- Configuration MinIO ---
fs = s3fs.S3FileSystem(
    key=os.environ["AWS_ACCESS_KEY_ID"],
    secret=os.environ["AWS_SECRET_ACCESS_KEY"],
    token=os.environ["AWS_SESSION_TOKEN"],
    client_kwargs={"endpoint_url": "https://minio.lab.sspcloud.fr"}
)
# --- Constantes ---
BUCKET = "thomasguinhut/carnet_partitions"
DOSSIER_PARTITIONS = "partitions_individuelles"
NOM_PAGE_GARDE = f"{BUCKET}/page_garde.pdf"
FICHIER_FINAL_BASE = f"{BUCKET}/fichier_fusionne_A5"
COMPRESSION_QUALITE = 90  # Qualité de compression JPEG (0-100)
A5_LANDSCAPE = landscape(A5)
A5_WIDTH, A5_HEIGHT = A5_LANDSCAPE


def lire_liste_musiques_depuis_minio() -> pd.DataFrame:
    with fs.open(f"{BUCKET}/liste.csv") as f:
        bdd = pd.read_csv(f)
    return bdd[bdd["JOUE"] == 1]


def generer_liste_fichiers_pdf(musiques: pd.DataFrame) -> list[str]:
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
    return noms_fichiers


def convertir_page_dans_A5_paysage_compressé(pdf_path: str) -> BytesIO:
    writer = PdfWriter()
    with fs.open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_buffer = BytesIO()
        img.save(img_buffer, format="JPEG", quality=COMPRESSION_QUALITE)
        img_buffer.seek(0)
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A5_LANDSCAPE)
        img_width_pts = img.width * 72 / 300
        img_height_pts = img.height * 72 / 300
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


def fusionner_pdfs_et_sauvegarder(pdfs_a_traiter: list[str], fichier_final: str, rotated: bool = False) -> None:
    merger = PdfMerger()
    for pdf_path in pdfs_a_traiter:
        pdf_converti = convertir_page_dans_A5_paysage_compressé(pdf_path)
        merger.append(PdfReader(pdf_converti))

    # Appliquer la rotation uniquement après la fusion complète
    if rotated:
        output = BytesIO()
        merger.write(output)
        output.seek(0)
        final_pdf = PdfReader(output)
        final_writer = PdfWriter()
        for i, page in enumerate(final_pdf.pages):
            if i >= 1 and i % 2 == 1:  # À partir de la 2ème page, une page sur deux
                page.rotate(180)
            final_writer.add_page(page)
        with fs.open(fichier_final, "wb") as f_out:
            final_writer.write(f_out)
    else:
        with fs.open(fichier_final, "wb") as f_out:
            merger.write(f_out)
    merger.close()
    print(f"✅ PDF final stocké dans MinIO : {fichier_final}")


def main(rotated: bool = False) -> None:
    musiques = lire_liste_musiques_depuis_minio()
    noms_fichiers = generer_liste_fichiers_pdf(musiques)
    pdfs_a_traiter = []
    if fs.exists(NOM_PAGE_GARDE):
        pdfs_a_traiter.append(NOM_PAGE_GARDE)
    pdfs_a_traiter.extend([
        f"{BUCKET}/{DOSSIER_PARTITIONS}/{nom}"
        for nom in noms_fichiers
        if fs.exists(f"{BUCKET}/{DOSSIER_PARTITIONS}/{nom}")
    ])
    suffixe = "_rotated" if rotated else ""
    fichier_final = f"{FICHIER_FINAL_BASE}{suffixe}.pdf"
    fusionner_pdfs_et_sauvegarder(pdfs_a_traiter, fichier_final, rotated=rotated)


if __name__ == "__main__":
    main(rotated=False)
    main(rotated=True)
