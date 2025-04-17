import qrcode

def gerar_payload_pix(valor, chave_pix, nome_recebedor="JOSE ALVES DOS ANJOS PA", cidade="CAICO", txid="TX12345678"):
    def format_field(id_, value):
        return f"{id_}{len(value):02d}{value}"

    gui = format_field("00", "br.gov.bcb.pix")
    chave = format_field("01", chave_pix)
    merchant_account_info = format_field("26", gui + chave)

    valor_str = f"{float(valor):.2f}"

    payload = (
        format_field("00", "01") +  # Payload Format Indicator
        merchant_account_info +     # Campo 26 (domínio + chave)
        format_field("52", "0000") +  # Merchant Category Code (padrão)
        format_field("53", "986") +   # Moeda BRL
        format_field("54", valor_str) +
        format_field("58", "BR") +
        format_field("59", nome_recebedor.upper()[:25]) +  # Sem acentos e máx 25
        format_field("60", cidade.upper()[:15]) +           # Sem acentos e máx 15
        format_field("62", format_field("05", txid[:35]))   # Campo adicional com TXID
    )

    # Campo CRC (ID 63, fixo com "6304" + valor calculado)
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


def gerar_qrcode_pix(valor, txid="TX12345678", output_path="qrcode_pix.png"):
    from django.conf import settings
    payload = gerar_payload_pix(
        valor,
        chave_pix=settings.PIX_CHAVE,
        nome_recebedor=settings.PIX_NOME_RECEBEDOR,
        cidade=settings.PIX_CIDADE,
        txid=txid
    )
    img = qrcode.make(payload)
    img.save(output_path)
    return output_path
