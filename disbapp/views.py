import os
import base64
import qrcode
from io import BytesIO
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.decorators import login_required
from weasyprint import HTML
from PyPDF2 import PdfMerger
from .utils.xml_consulta import ler_nfe_xml
from .utils.qr_generator import gerar_qrcode_pix, gerar_txid_seguro

def formatar_valor(valor):
    try:
        valor_float = float(valor.replace(",", "."))
        return f"{valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

@login_required
def upload_xml_nfe_view(request):
    if request.method == "POST" and request.FILES.getlist("xml"):
        arquivos_xml = request.FILES.getlist("xml")
        cidade_escolhida = request.POST.get("cidade", "").strip().replace(" ", "_").upper()
        config_pix = settings.PIX_CONFIGS.get(cidade_escolhida)


        if not config_pix:
            return JsonResponse({"erro": "Cidade inválida."}, status=400)

        base_dir = os.path.dirname(__file__)
        response_data = []
        merger = PdfMerger()

        for xml_file in arquivos_xml:
            caminho_temp = os.path.join(base_dir, "temp_nfe.xml")
            with open(caminho_temp, "wb+") as f:
                for chunk in xml_file.chunks():
                    f.write(chunk)

            dados = ler_nfe_xml(caminho_temp)
            valor = dados.get("valor_liquido", "0")
            valor_float = float(valor.replace(",", "."))
            valor_formatado = formatar_valor(valor)
            numero_nota = dados.get("txid", "0")

            caminho_qr = os.path.join(base_dir, "qrcode_pix.png")
            caminho_qr, payload = gerar_qrcode_pix(
                valor=valor_float,
                numero_nota=numero_nota,
                output_path=caminho_qr,
                chave_pix=config_pix["chave"],
                nome_recebedor=config_pix["nome"],
                cidade=config_pix["cidade"]
            )

            with open(caminho_qr, "rb") as qr_file:
                qrcode_base64 = base64.b64encode(qr_file.read()).decode("utf-8")

            html_string = render_to_string("pdf/nota_pdf.html", {
                "txid": dados.get("txid"),
                "valor": valor_formatado,
                "cliente": dados.get("cliente", "N/A"),
                "cod_cliente": dados.get("cod_cliente", "N/A"),
                "payload": payload,
                "qrcode_base64": qrcode_base64,
                "cidade": config_pix["cidade"],
                "chave_pix": config_pix["chave"]
            })

            pdf_buffer = BytesIO()
            HTML(string=html_string).write_pdf(pdf_buffer)
            pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode("utf-8")

            pdf_buffer.seek(0)
            merger.append(pdf_buffer)

            dados["txid"] = dados.get("txid")
            dados["valor_liquido"] = valor_formatado
            dados["qrcode_base64"] = qrcode_base64
            dados["payload"] = payload
            dados["pdf_base64"] = pdf_base64
            dados["cidade"] = config_pix["cidade"]

            response_data.append(dados)

            os.remove(caminho_temp)
            os.remove(caminho_qr)

        final_pdf = BytesIO()
        merger.write(final_pdf)
        merger.close()
        final_pdf_base64 = base64.b64encode(final_pdf.getvalue()).decode("utf-8")

        return JsonResponse({
            "notas": response_data,
            "pdf_unico_base64": final_pdf_base64
        })

    return JsonResponse({"erro": "Envie arquivos XML via POST."}, status=400)


@login_required
def pagina_upload_view(request):
    return render(request, "nfe.html")
