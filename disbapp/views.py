import os
import base64
import qrcode
from io import BytesIO
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML

from .utils.xml_consulta import ler_nfe_xml
from .utils.qr_generator import gerar_payload_pix


def upload_xml_nfe_view(request):
    if request.method == "POST" and request.FILES.getlist("xml"):
        arquivos_xml = request.FILES.getlist("xml")
        base_dir = os.path.dirname(__file__)
        response_data = []

        for xml_file in arquivos_xml:
            caminho_temp = os.path.join(base_dir, "temp_nfe.xml")

            # Salvar XML temporário
            with open(caminho_temp, "wb+") as f:
                for chunk in xml_file.chunks():
                    f.write(chunk)

            dados = ler_nfe_xml(caminho_temp)
            valor = dados.get("valor_total", "0").replace(",", ".")
            txid = dados.get("chave") or "TX12345678"
            txid = txid.strip()[:35] or "TX12345678"

            # Gerar payload e QR Code
            payload = gerar_payload_pix(
                valor,
                chave_pix=settings.PIX_CHAVE,
                nome_recebedor=settings.PIX_NOME_RECEBEDOR,
                cidade=settings.PIX_CIDADE,
                txid=txid
            )

            # Gerar QR code em memória
            qr_img = qrcode.make(payload)
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format="PNG")
            qrcode_base64 = base64.b64encode(qr_buffer.getvalue()).decode("utf-8")

            # Geração do PDF (com template HTML)
            html_string = render_to_string("pdf/nota_pdf.html", {
                "txid": txid,
                "valor": valor,
                "cliente": dados.get("cliente", ""),
                "payload": payload,
                "qrcode_base64": qrcode_base64
            })

            pdf_buffer = BytesIO()
            HTML(string=html_string).write_pdf(pdf_buffer)
            pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode("utf-8")

            # Montar resposta
            dados["txid"] = txid
            dados["qrcode_base64"] = qrcode_base64
            dados["payload"] = payload
            dados["pdf_base64"] = pdf_base64

            response_data.append(dados)

            os.remove(caminho_temp)

        return JsonResponse(response_data, safe=False)

    return JsonResponse({"erro": "Envie arquivos XML via POST."}, status=400)

def pagina_upload_view(request):
    return render(request, "nfe.html")
