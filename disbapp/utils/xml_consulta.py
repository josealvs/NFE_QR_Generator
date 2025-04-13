import xml.etree.ElementTree as ET

def ler_nfe_xml(path_arquivo):
    tree = ET.parse(path_arquivo)
    root = tree.getroot()

    ns = {'ns': root.tag.split('}')[0].strip('{')}  # namespace dinâmico

    emitente = root.find('.//ns:emit/ns:xNome', ns).text
    cnpj = root.find('.//ns:emit/ns:CNPJ', ns).text
    data_emissao = root.find('.//ns:ide/ns:dhEmi', ns).text
    valor_total = root.find('.//ns:ICMSTot/ns:vNF', ns).text
    chave = root.attrib.get('Id', '')[-44:]

    produtos = []
    for det in root.findall('.//ns:det', ns):
        nome = det.find('.//ns:prod/ns:xProd', ns).text
        qtd = det.find('.//ns:prod/ns:qCom', ns).text
        valor = det.find('.//ns:prod/ns:vProd', ns).text
        produtos.append({'nome': nome, 'quantidade': qtd, 'valor_total': valor})

    return {
        'chave': chave,
        'emitente': emitente,
        'cnpj_emitente': cnpj,
        'data_emissao': data_emissao,
        'valor_total': valor_total,
        'produtos': produtos
    }
