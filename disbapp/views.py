import os
import csv
import base64
from io import BytesIO, StringIO
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from weasyprint import HTML
from PyPDF2 import PdfMerger
from .utils.xml_consulta import ler_nfe_xml
from .utils.qr_generator import gerar_qrcode_pix

@login_required
def upload_xml_nfe_view(request):
    if request.method == "POST" and request.FILES.getlist("xml"):
        arquivos_xml = request.FILES.getlist("xml")
        cidade_escolhida = request.POST.get("cidade", "").strip().replace(" ", "_").upper()
        config_pix = settings.PIX_CONFIGS.get(cidade_escolhida)

        if not config_pix:
            return JsonResponse({"erro": "Cidade inválida."}, status=400)

        base_dir = os.path.dirname(__file__)
        merger = PdfMerger()
        response_data = []

        agrupado_por_cliente = {}

        for xml_file in arquivos_xml:
            caminho_temp = os.path.join(base_dir, "temp_nfe.xml")
            with open(caminho_temp, "wb+") as f:
                for chunk in xml_file.chunks():
                    f.write(chunk)

            dados = ler_nfe_xml(caminho_temp)
            os.remove(caminho_temp)

            cod_cliente = dados.get("cod_cliente") or f"NF_{dados.get('txid')}"
            if cod_cliente not in agrupado_por_cliente:
                agrupado_por_cliente[cod_cliente] = {
                    "cliente": dados.get("cliente", "N/A"),
                    "ident_cliente": dados.get("ident_cliente", ""),
                    "cidade": config_pix["cidade"],
                    "notas": [],
                    "valor_total": 0.0
                }

            valor_float = float(dados.get("valor_liquido", "0").replace(",", "."))
            agrupado_por_cliente[cod_cliente]["notas"].append({
                "txid": dados.get("txid"),
                "valor": valor_float,
                "valor_formatado": f"{valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "data_emissao": dados.get("data_emissao", "N/A")
            })
            agrupado_por_cliente[cod_cliente]["valor_total"] += valor_float

        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)
        csv_writer.writerow(["Codigo do Cliente", "Notas Fiscais", "Valor Total", "Cliente", "CPF/CNPJ", "Cidade"])

        for cod_cliente, grupo in agrupado_por_cliente.items():
            nota_numeros = [n["txid"] for n in grupo["notas"]]
            valor_total = grupo["valor_total"]
            valor_formatado = f"{valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            notas_concatenadas = "/".join(nota_numeros)
            usar_cod_como_txid = len(nota_numeros) > 1 and not cod_cliente.startswith("NF_")
            txid = cod_cliente if usar_cod_como_txid else nota_numeros[0]

            caminho_qr = os.path.join(base_dir, f"qrcode_pix_{txid}.png")
            caminho_qr, payload = gerar_qrcode_pix(
                valor=valor_total,
                numero_nota=txid,
                chave_pix=config_pix["chave"],
                nome_recebedor=config_pix["nome"],
                cidade=config_pix["cidade"],
                output_path=caminho_qr
            )

            with open(caminho_qr, "rb") as qr_file:
                qrcode_base64 = base64.b64encode(qr_file.read()).decode("utf-8")
            os.remove(caminho_qr)

            # Carrega logo e converte para base64
            caminho_logo = os.path.join(settings.BASE_DIR, 'disbapp', 'static', 'image.png')
            with open(caminho_logo, 'rb') as logo_file:
                logo_base64 = base64.b64encode(logo_file.read()).decode('utf-8')

            html_string = render_to_string("pdf/nota_pdf.html", {
                "valor": valor_formatado,
                "cliente": grupo["cliente"],
                "cod_cliente": cod_cliente,
                "payload": payload,
                "qrcode_base64": qrcode_base64,
                "cidade": grupo["cidade"],
                "notas_concatenadas": notas_concatenadas,
                "logo": logo_base64
            })

            pdf_buffer = BytesIO()
            HTML(string=html_string).write_pdf(pdf_buffer)
            pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode("utf-8")
            pdf_buffer.seek(0)
            merger.append(pdf_buffer)

            response_data.append({
                "valor_liquido": valor_formatado,
                "cliente": grupo["cliente"],
                "cod_cliente": cod_cliente,
                "ident_cliente": grupo["ident_cliente"],
                "notas_concatenadas": notas_concatenadas,
                "payload": payload,
                "qrcode_base64": qrcode_base64,
                "pdf_base64": pdf_base64,
                "cidade": grupo["cidade"]
            })

            csv_writer.writerow([
                cod_cliente,
                notas_concatenadas,
                valor_formatado,
                grupo["cliente"],
                grupo["ident_cliente"],
                grupo["cidade"]
            ])

        final_pdf = BytesIO()
        merger.write(final_pdf)
        merger.close()
        final_pdf_base64 = base64.b64encode(final_pdf.getvalue()).decode("utf-8")

        csv_buffer.seek(0)
        csv_bytes = csv_buffer.getvalue().encode("utf-8")
        csv_base64 = base64.b64encode(csv_bytes).decode("utf-8")

        data_hoje = timezone.localtime().date().isoformat()
        csv_filename = f"conciliacao_{data_hoje}.csv"

        return JsonResponse({
            "notas": response_data,
            "pdf_unico_base64": final_pdf_base64,
            "csv_base64": csv_base64,
            "csv_filename": csv_filename
        })

    return JsonResponse({"erro": "Envie arquivos XML via POST."}, status=400)

@login_required
def pagina_upload_view(request):
    return render(request, "nfe.html")
