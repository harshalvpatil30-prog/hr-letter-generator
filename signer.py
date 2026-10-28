from pyhanko.sign import signers, fields
from pyhanko.stamp import TextStampStyle
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter

from config import P12_PATH, P12_PASSWORD
from style import ANCHOR


def sign_pdf(in_path: str, reason: str = "Issued by HR Department",
             box=None, page=None) -> str:
    """Sign a PDF. By default the stamp goes into the space the signature block reserved."""
    if box is None:
        box = ANCHOR.get("box")
        if box is None:
            raise RuntimeError("Signature position was not recorded. "
                               "Generate the PDF in the same run, just before signing.")
        page = -1            # the signature block is always on the last page
    elif page is None:
        page = 0

    out_path = in_path.replace(".pdf", "_signed.pdf")

    signer = signers.SimpleSigner.load_pkcs12(pfx_file=P12_PATH, passphrase=P12_PASSWORD)
    meta = signers.PdfSignatureMetadata(
        field_name="HR_Signature", reason=reason, location="Pune, India")
    stamp = TextStampStyle(
        stamp_text="Digitally signed by: %(signer)s\nDate: %(ts)s", border_width=1)
    pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp)

    with open(in_path, "rb") as inf:
        writer = IncrementalPdfFileWriter(inf)
        fields.append_signature_field(
            writer, fields.SigFieldSpec("HR_Signature", box=box, on_page=page))
        with open(out_path, "wb") as outf:
            pdf_signer.sign_pdf(writer, output=outf)

    return out_path