import re
import xml.etree.ElementTree as ET

def ler_nfe_xml(path_arquivo):
    tree = ET.parse(path_arquivo)
    root = tree.getroot()
    ns = {'ns': root.tag.split('}')[0].strip('{')}  # namespace dinâmico

    def get_text(path):
        el = root.find(path, ns)
        return el.text.strip() if el is not None and el.text else ""

    cliente = get_text('.//ns:dest/ns:xNome')
    cpf_cliente = get_text('.//ns:dest/ns:CPF')
    cnpj_cliente = get_text('.//ns:dest/ns:CNPJ')
    data_emissao = get_text('.//ns:ide/ns:dhEmi')
    valor_liquido = get_text('.//ns:fat/ns:vLiq')
    txid = get_text('.//ns:ide/ns:nNF')
    tpag = get_text('.//ns:detPag/ns:tPag')

    inf_cpl = get_text('.//ns:infAdic/ns:infCpl')
    cod_cliente = ""

    if inf_cpl:
        match = re.search(r'V[^V]*V(\d+)\|', inf_cpl)
        if match:
            cod_cliente = match.group(1)

    return {
        'txid': txid,
        'cliente': cliente,
        'ident_cliente': cpf_cliente if cpf_cliente else cnpj_cliente,
        'data_emissao': data_emissao,
        'valor_liquido': valor_liquido,
        'cod_cliente': cod_cliente,
        'tpag': tpag  # adicionado
    }
