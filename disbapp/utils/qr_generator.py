import qrcode
import unicodedata
import re
from django.conf import settings

def limpar_texto_pix(texto, max_len):
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r'[^A-Z0-9 ]', '', texto.upper())
    return texto.strip()[:max_len]

def gerar_txid_seguro(numero_nota: str):
    """Gera um TXID seguro e compatível com o padrão EMVCo a partir do número da nota."""
    numero = re.sub(r'\D', '', numero_nota)  # remove caracteres não numéricos
    numero = numero.zfill(8)  # força ao menos 8 dígitos
    return f"TX{numero}"[:35]  # prefixo + truncamento (máx 35 chars)

def format_field(id_, value):
    return f"{id_}{len(value):02d}{value}"

def gerar_payload_pix(valor, chave_pix, nome_recebedor="", cidade="CIDADE", txid="TX12345678"):
    nome_recebedor = limpar_texto_pix(nome_recebedor, 25)
    cidade = limpar_texto_pix(cidade, 15)
    txid = limpar_texto_pix(txid, 35) or "TX12345678"
    valor_str = f"{float(valor):.2f}"

    gui = format_field("00", "br.gov.bcb.pix")
    chave = format_field("01", chave_pix)
    merchant_account_info = format_field("26", gui + chave)

    payload = (
        format_field("00", "01") +
        merchant_account_info +
        format_field("52", "0000") +
        format_field("53", "986") +
        format_field("54", valor_str) +
        format_field("58", "BR") +
        format_field("59", nome_recebedor) +
        format_field("60", cidade) +
        format_field("62", format_field("05", txid))
    )

    payload_com_crc = payload + "6304"
    crc = crc16(payload_com_crc.encode("utf-8"))
    payload_final = payload_com_crc + f"{crc:04X}"
    return payload_final

def crc16(data: bytes):
    poly = 0x1021
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc

def gerar_qrcode_pix(valor, numero_nota, output_path="qrcode_pix.png"):
    txid = gerar_txid_seguro(numero_nota)
    payload = gerar_payload_pix(
        valor=valor,
        chave_pix=settings.PIX_CHAVE,
        nome_recebedor=settings.PIX_NOME_RECEBEDOR,
        cidade=settings.PIX_CIDADE,
        txid=txid
    )
    img = qrcode.make(payload)
    img.save(output_path)
    return output_path, payload
