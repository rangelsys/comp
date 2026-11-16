"""
Entrega 2 — análise sintática.
Parser manual por descida recursiva.
Constrói a Árvore Sintática Abstrata (AST).
"""

from mplc.erros import ErroMPL


# ==========================================
# 1. CLASSES DA ÁRVORE SINTÁTICA (AST)
# ==========================================

class NoArvore:
    def despejar(self, nivel=0):
        return []


class Programa(NoArvore):
    def __init__(self, funcoes):
        self.funcoes = funcoes

    def despejar(self, nivel=0):
        linhas = ["  " * nivel + "programa"]
        for f in self.funcoes:
            linhas.extend(f.despejar(nivel + 1))
        return linhas


class Funcao(NoArvore):
    def __init__(self, nome, tipo_retorno, parametros, bloco, linha):
        self.nome = nome
        self.tipo_retorno = tipo_retorno
        self.parametros = parametros
        self.bloco = bloco
        self.linha = linha

    def despejar(self, nivel=0):
        linhas = [
            "  " * nivel +
            f"funcao {self.nome} {self.tipo_retorno}"
        ]

        linhas.append("  " * (nivel + 1) + "parametros")

        for p in self.parametros:
            linhas.extend(p.despejar(nivel + 2))

        linhas.extend(self.bloco.despejar(nivel + 1))
        return linhas


class Parametro(NoArvore):
    def __init__(self, nome, tipo, linha):
        self.nome = nome
        self.tipo = tipo
        self.linha = linha

    def despejar(self, nivel=0):
        return [
            "  " * nivel + f"parametro {self.nome} {self.tipo}"
        ]


class Bloco(NoArvore):
    def __init__(self, comandos, linha=1):
        self.comandos = comandos
        self.linha = linha

    def despejar(self, nivel=0):
        linhas = ["  " * nivel + "bloco"]

        for cmd in self.comandos:
            linhas.extend(cmd.despejar(nivel + 1))

        return linhas


class Escreva(NoArvore):
    def __init__(self, expressao, linha=1):
        self.expressao = expressao
        self.linha = linha

    def despejar(self, nivel=0):
        linhas = ["  " * nivel + "escreva"]
        linhas.extend(self.expressao.despejar(nivel + 1))
        return linhas


class Declaracao(NoArvore):
    def __init__(self, nome, tipo, expr=None, linha=1):
        self.nome = nome
        self.tipo = tipo
        self.expr = expr
        self.linha = linha

    def despejar(self, nivel=0):
        linhas = [
            "  " * nivel + f"declaracao {self.nome} {self.tipo}"
        ]

        if self.expr is not None:
            linhas.extend(self.expr.despejar(nivel + 1))

        return linhas


class Atribuicao(NoArvore):
    def __init__(self, nome, expr, linha=1):
        self.nome = nome
        self.expr = expr
        self.linha = linha

    def despejar(self, nivel=0):
        linhas = ["  " * nivel + f"atribuicao {self.nome}"]
        linhas.extend(self.expr.despejar(nivel + 1))
        return linhas


class Se(NoArvore):
    def __init__(self, cond, bloco_entao, bloco_senao=None, linha=1):
        self.cond = cond
        self.bloco_entao = bloco_entao
        self.bloco_senao = bloco_senao
        self.linha = linha

    def despejar(self, nivel=0):
        linhas = ["  " * nivel + "se"]
        linhas.extend(self.cond.despejar(nivel + 1))
        linhas.extend(self.bloco_entao.despejar(nivel + 1))

        if self.bloco_senao is not None:
            linhas.extend(self.bloco_senao.despejar(nivel + 1))

        return linhas


class Enquanto(NoArvore):
    def __init__(self, cond, bloco, linha=1):
        self.cond = cond
        self.bloco = bloco
        self.linha = linha

    def despejar(self, nivel=0):
        linhas = ["  " * nivel + "enquanto"]
        linhas.extend(self.cond.despejar(nivel + 1))
        linhas.extend(self.bloco.despejar(nivel + 1))
        return linhas


class Retorne(NoArvore):
    def __init__(self, expr=None, linha=1):
        self.expr = expr
        self.linha = linha

    def despejar(self, nivel=0):
        linhas = ["  " * nivel + "retorne"]

        if self.expr is not None:
            linhas.extend(self.expr.despejar(nivel + 1))

        return linhas


class Chamada(NoArvore):
    def __init__(self, nome, args, linha=1):
        self.nome = nome
        self.args = args
        self.linha = linha

    def despejar(self, nivel=0):
        linhas = ["  " * nivel + f"chamada {self.nome}"]

        for arg in self.args:
            linhas.extend(arg.despejar(nivel + 1))

        return linhas


class Binario(NoArvore):
    def __init__(self, op, esquerda, direita, linha=1):
        self.op = op
        self.esquerda = esquerda
        self.direita = direita
        self.linha = linha

    def despejar(self, nivel=0):
        linhas = ["  " * nivel + f"binario {self.op}"]
        linhas.extend(self.esquerda.despejar(nivel + 1))
        linhas.extend(self.direita.despejar(nivel + 1))
        return linhas


class Unario(NoArvore):
    def __init__(self, op, operando, linha=1):
        self.op = op
        self.operando = operando
        self.linha = linha

    def despejar(self, nivel=0):
        linhas = ["  " * nivel + f"unario {self.op}"]
        linhas.extend(self.operando.despejar(nivel + 1))
        return linhas


class Literal(NoArvore):
    def __init__(self, tipo, valor, linha=1):
        self.tipo = tipo
        self.valor = valor
        self.linha = linha

    def despejar(self, nivel=0):
        return [
            "  " * nivel +
            f"literal {self.tipo} {self.valor}"
        ]


class Variavel(NoArvore):
    def __init__(self, nome, linha=1):
        self.nome = nome
        self.linha = linha

    def despejar(self, nivel=0):
        return ["  " * nivel + f"variavel {self.nome}"]


# ==========================================
# 2. PARSER
# ==========================================

TIPOS = {
    'TIPO_INTEIRO': 'inteiro',
    'TIPO_REAL': 'real',
    'TIPO_LOGICO': 'logico',
    'TIPO_TEXTO': 'texto',
    'TIPO_VAZIO': 'vazio'
}

TIPOS_DADOS = {
    'TIPO_INTEIRO',
    'TIPO_REAL',
    'TIPO_LOGICO',
    'TIPO_TEXTO'
}


OPERADORES = {
    'OU': 'ou',
    'E': 'e',
    'IGUAL': '==',
    'DIFERENTE': '!=',
    'MENOR': '<',
    'MENOR_IGUAL': '<=',
    'MAIOR': '>',
    'MAIOR_IGUAL': '>=',
    'MAIS': '+',
    'MENOS': '-',
    'VEZES': '*',
    'DIVIDE': '/',
    'RESTO': '%'
}


class Parser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.posicao = 0

    def atual(self):
        return self.tokens[self.posicao]

    def verificar(self, tipo):
        return self.atual().tipo == tipo

    def avancar(self):
        token = self.atual()

        if token.tipo != 'FIM_ARQUIVO':
            self.posicao += 1

        return token

    def aceitar(self, tipo):
        if self.verificar(tipo):
            return self.avancar()

        return None

    def erro(self, mensagem):
        token = self.atual()

        raise ErroMPL(
            'sintatico',
            token.linha,
            token.coluna,
            mensagem
        )

    def esperar(self, tipo, mensagem=None):
        if self.verificar(tipo):
            return self.avancar()

        if mensagem is None:
            mensagem = f"esperado {tipo}, encontrado {self.atual().lexema}"

        self.erro(mensagem)

    # ======================================
    # 3. ESTRUTURA DO PROGRAMA
    # ======================================

    def analisar(self):
        funcoes = []

        while not self.verificar('FIM_ARQUIVO'):
            funcoes.append(self.funcao())

        return Programa(funcoes)

    def tipo_retorno(self):
        token = self.atual()

        if token.tipo in TIPOS:
            self.avancar()
            return TIPOS[token.tipo]

        self.erro("tipo de retorno esperado")

    def tipo_dado(self):
        token = self.atual()

        if token.tipo in TIPOS_DADOS:
            self.avancar()
            return TIPOS[token.tipo]

        self.erro("tipo de dado esperado")

    def funcao(self):
        self.esperar('FUNCAO')
        tipo = self.tipo_retorno()

        nome = self.esperar('ID', "nome da funcao esperado")

        self.esperar('ABRE_PAR')

        parametros = []

        if not self.verificar('FECHA_PAR'):
            parametros.append(self.parametro())

            while self.aceitar('VIRGULA'):
                parametros.append(self.parametro())

        self.esperar('FECHA_PAR')

        bloco = self.bloco()

        return Funcao(
            nome.lexema,
            tipo,
            parametros,
            bloco,
            nome.linha
        )

    def parametro(self):
        tipo = self.tipo_dado()
        nome = self.esperar('ID', "nome do parametro esperado")

        return Parametro(nome.lexema, tipo, nome.linha)

    # ======================================
    # 4. COMANDOS E BLOCOS
    # ======================================

    def bloco(self):
        linha = self.atual().linha
        self.esperar('ABRE_CHAVE')

        comandos = []

        while not self.verificar('FECHA_CHAVE'):
            if self.verificar('FIM_ARQUIVO'):
                self.erro("bloco nao fechado")

            comandos.append(self.comando())

        self.esperar('FECHA_CHAVE')

        return Bloco(comandos, linha)

    def comando(self):

        if self.verificar('TIPO_INTEIRO') or \
           self.verificar('TIPO_REAL') or \
           self.verificar('TIPO_LOGICO') or \
           self.verificar('TIPO_TEXTO'):
            return self.declaracao()

        if self.verificar('ESCREVA'):
            return self.escreva()

        if self.verificar('SE'):
            return self.condicional()

        if self.verificar('ENQUANTO'):
            return self.repeticao()

        if self.verificar('RETORNE'):
            return self.retorno()

        if self.verificar('ABRE_CHAVE'):
            return self.bloco()

        if self.verificar('ID'):
            return self.atribuicao_ou_chamada()

        self.erro("comando inesperado")

    def declaracao(self):
        linha = self.atual().linha
        tipo = self.tipo_dado()

        nome = self.esperar('ID', "nome da variavel esperado")

        expr = None

        if self.aceitar('ATRIBUI'):
            expr = self.expressao()

        self.esperar(
            'PONTO_VIRGULA',
            "esperado ponto e virgula"
        )

        return Declaracao(nome.lexema, tipo, expr, linha)

    def atribuicao_ou_chamada(self):
        nome = self.atual()

        if self.posicao + 1 < len(self.tokens) and \
           self.tokens[self.posicao + 1].tipo == 'ABRE_PAR':

            chamada = self.chamada()

            self.esperar('PONTO_VIRGULA')

            return chamada

        linha = self.atual().linha
        self.avancar()

        self.esperar('ATRIBUI', "esperado operador de atribuicao")

        expr = self.expressao()

        self.esperar('PONTO_VIRGULA')

        return Atribuicao(nome.lexema, expr, linha)

    def escreva(self):
        linha = self.atual().linha
        self.esperar('ESCREVA')
        self.esperar('ABRE_PAR')

        expr = self.expressao()

        self.esperar('FECHA_PAR')
        self.esperar('PONTO_VIRGULA')

        return Escreva(expr, linha)

    def condicional(self):
        linha = self.atual().linha
        self.esperar('SE')
        self.esperar('ABRE_PAR')

        cond = self.expressao()

        self.esperar('FECHA_PAR')

        bloco_entao = self.bloco()

        bloco_senao = None

        if self.aceitar('SENAO'):
            bloco_senao = self.bloco()

        return Se(cond, bloco_entao, bloco_senao, linha)

    def repeticao(self):
        linha = self.atual().linha
        self.esperar('ENQUANTO')
        self.esperar('ABRE_PAR')

        cond = self.expressao()

        self.esperar('FECHA_PAR')

        bloco = self.bloco()

        return Enquanto(cond, bloco, linha)

    def retorno(self):
        linha = self.atual().linha
        self.esperar('RETORNE')

        expr = None

        if not self.verificar('PONTO_VIRGULA'):
            expr = self.expressao()

        self.esperar('PONTO_VIRGULA')

        return Retorne(expr, linha)

    # ======================================
    # 5. EXPRESSÕES
    # DESCIDA RECURSIVA POR PRECEDÊNCIA
    # ======================================

    def expressao(self):
        return self.ou()

    # Nível 1: OU

    def ou(self):
        esquerda = self.e()

        while self.verificar('OU'):
            linha = self.atual().linha
            op = self.avancar().lexema
            direita = self.e()

            esquerda = Binario(op, esquerda, direita, linha)

        return esquerda

    # Nível 2: E

    def e(self):
        esquerda = self.igualdade()

        while self.verificar('E'):
            linha = self.atual().linha
            op = self.avancar().lexema
            direita = self.igualdade()

            esquerda = Binario(op, esquerda, direita, linha)

        return esquerda

    # Nível 3: == e !=

    def igualdade(self):
        esquerda = self.relacional()

        while self.verificar('IGUAL') or \
              self.verificar('DIFERENTE'):

            linha = self.atual().linha
            op = self.avancar().lexema
            direita = self.relacional()

            esquerda = Binario(op, esquerda, direita, linha)

        return esquerda

    # Nível 4: < <= > >=

    def relacional(self):
        esquerda = self.aditiva()

        while self.verificar('MENOR') or \
              self.verificar('MENOR_IGUAL') or \
              self.verificar('MAIOR') or \
              self.verificar('MAIOR_IGUAL'):

            linha = self.atual().linha
            op = self.avancar().lexema
            direita = self.aditiva()

            esquerda = Binario(op, esquerda, direita, linha)

        return esquerda

    # Nível 5: + e -

    def aditiva(self):
        esquerda = self.multiplicativa()

        while self.verificar('MAIS') or \
              self.verificar('MENOS'):

            linha = self.atual().linha
            op = self.avancar().lexema
            direita = self.multiplicativa()

            esquerda = Binario(op, esquerda, direita, linha)

        return esquerda

    # Nível 6: * / %

    def multiplicativa(self):
        esquerda = self.unaria()

        while self.verificar('VEZES') or \
              self.verificar('DIVIDE') or \
              self.verificar('RESTO'):

            linha = self.atual().linha
            op = self.avancar().lexema
            direita = self.unaria()

            esquerda = Binario(op, esquerda, direita, linha)

        return esquerda

    # Nível 7: nao e menos unário

    def unaria(self):
        if self.verificar('NAO'):
            linha = self.atual().linha
            op = self.avancar().lexema
            return Unario(op, self.unaria(), linha)

        if self.verificar('MENOS'):
            linha = self.atual().linha
            op = self.avancar().lexema
            return Unario(op, self.unaria(), linha)

        return self.primaria()

    # Nível 8: literais, variáveis, chamadas e parênteses

    def primaria(self):

        if self.verificar('INTEIRO'):
            linha = self.atual().linha
            token = self.avancar()
            return Literal('inteiro', token.lexema, linha)

        if self.verificar('REAL'):
            linha = self.atual().linha
            token = self.avancar()
            valor = f"{float(token.lexema):.6f}"
            return Literal('real', valor, linha)

        if self.verificar('LOGICO'):
            linha = self.atual().linha
            token = self.avancar()
            return Literal('logico', token.lexema, linha)

        if self.verificar('TEXTO'):
            linha = self.atual().linha
            token = self.avancar()
            return Literal('texto', token.lexema, linha)

        if self.verificar('ID'):

            if self.posicao + 1 < len(self.tokens) and \
               self.tokens[self.posicao + 1].tipo == 'ABRE_PAR':
                return self.chamada()

            linha = self.atual().linha
            token = self.avancar()
            return Variavel(token.lexema, linha)

        if self.aceitar('ABRE_PAR'):
            expr = self.expressao()
            self.esperar('FECHA_PAR')
            return expr

        self.erro("expressao esperada")

    # ======================================
    # 6. CHAMADAS DE FUNÇÃO
    # ======================================

    def chamada(self):
        linha = self.atual().linha
        nome = self.esperar('ID', "nome da funcao esperado")

        self.esperar('ABRE_PAR')

        argumentos = []

        if not self.verificar('FECHA_PAR'):
            argumentos.append(self.expressao())

            while self.aceitar('VIRGULA'):
                argumentos.append(self.expressao())

        self.esperar('FECHA_PAR')

        return Chamada(nome.lexema, argumentos, linha)


# ==========================================
# 7. INTERFACE USADA PELO PRINCIPAL.PY
# ==========================================

def analisar(tokens):
    parser = Parser(tokens)
    return parser.analisar()


def despejar(arvore):
    return arvore.despejar()