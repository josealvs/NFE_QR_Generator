import os
import base64
from django.http import JsonResponse
from .utils.xml_consulta import ler_nfe_xml
from .utils.qr_generator import gerar_qrcode_pix, gerar_payload_pix
from django.shortcuts import render
from django.conf import settings


def upload_xml_nfe_view(request):
    if request.method == "POST" and request.FILES.getlist("xml"):
        arquivos_xml = request.FILES.getlist("xml")

        base_dir = os.path.dirname(__file__)
        response_data = []

        for xml_file in arquivos_xml:
            caminho_temp = os.path.join(base_dir, "temp_nfe.xml")
            caminho_qr = os.path.join(base_dir, "qrcode_pix.png")

            # Salvar arquivo temporário
            with open(caminho_temp, "wb+") as f:
                for chunk in xml_file.chunks():
                    f.write(chunk)

            # Lê o XML e extrai os dados
            dados = ler_nfe_xml(caminho_temp)
            valor = dados.get("valor_total", "0").replace(",", ".")
            txid = dados.get("chave") or "TX12345678"
            txid = txid.strip()[:35] or "TX12345678"

            # Gera o QR Code e salva a imagem
            gerar_qrcode_pix(valor, txid=txid, output_path=caminho_qr)

            # Retorna o QR Code como base64
            with open(caminho_qr, "rb") as qr_file:
                qrcode_base64 = base64.b64encode(qr_file.read()).decode("utf-8")

            # Monta o payload
            payload = gerar_payload_pix(
                valor,
                chave_pix=settings.PIX_CHAVE,
                nome_recebedor=settings.PIX_NOME_RECEBEDOR,
                cidade=settings.PIX_CIDADE,
                txid=txid
            )

            # Adiciona o QR Code e payload aos dados
            dados["qrcode_base64"] = qrcode_base64
            dados["payload"] = payload

            # Adiciona os dados à resposta
            response_data.append(dados)

            # Limpeza dos arquivos temporários
            os.remove(caminho_temp)
            os.remove(caminho_qr)

        return JsonResponse(response_data, safe=False)  # Retorna uma lista de respostas

    return JsonResponse({"erro": "Envie arquivos XML via POST."}, status=400)


def pagina_upload_view(request):
    return render(request, "nfe.html")
