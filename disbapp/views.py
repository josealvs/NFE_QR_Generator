import os
import base64
from django.http import JsonResponse
from .utils.xml_consulta import ler_nfe_xml
from .utils.qr_generator import gerar_qrcode_pix
from django.shortcuts import render
from .utils.qr_generator import gerar_qrcode_pix, gerar_payload_pix
from django.conf import settings


def upload_xml_nfe_view(request):
    if request.method == "POST" and request.FILES.get("xml"):
        xml_file = request.FILES["xml"]

        base_dir = os.path.dirname(__file__)
        caminho_temp = os.path.join(base_dir, "temp_nfe.xml")
        caminho_qr = os.path.join(base_dir, "qrcode_pix.png")

        # Salvar arquivo temporário
        with open(caminho_temp, "wb+") as f:
            for chunk in xml_file.chunks():
                f.write(chunk)

        dados = ler_nfe_xml(caminho_temp)
        valor = dados.get("valor_total", "0").replace(",", ".")

        # Usa a chave da NF-e como TXID (opcional)
        txid = dados.get("chave") or "TX12345678"
        txid = txid.strip()[:35] or "TX12345678"


        gerar_qrcode_pix(valor, txid=txid, output_path=caminho_qr)

        # Retornar QR Code como base64
        with open(caminho_qr, "rb") as qr_file:
            qrcode_base64 = base64.b64encode(qr_file.read()).decode("utf-8")

        dados["qrcode_base64"] = qrcode_base64
        
        payload = gerar_payload_pix(
            valor,
            chave_pix=settings.PIX_CHAVE,
            nome_recebedor=settings.PIX_NOME_RECEBEDOR,
            cidade=settings.PIX_CIDADE,
            txid=txid
        )


        # depois de gerar o QR Code
        dados["payload"] = payload

        # Limpeza dos arquivos
        os.remove(caminho_temp)
        os.remove(caminho_qr)

        return JsonResponse(dados)

    return JsonResponse({"erro": "Envie um arquivo XML via POST."}, status=400)


def pagina_upload_view(request):
    return render(request, "nfe.html")
