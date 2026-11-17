
"""
Entrega 4, segunda metade — geracao do codigo executavel.
"""


def gerar(codigo_intermediario):
    linhas = []

    for instrucao in codigo_intermediario:
        # Serializa as instruções usando o formato nativo do Python.
        linhas.append(repr(instrucao))

    return linhas
