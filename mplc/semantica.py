"""Entrega 3 — análise semântica da MPL."""

from dataclasses import dataclass, field
from mplc.erros import ErroMPL
from mplc import sintatico as ast


@dataclass
class Simbolo:
    nome: str
    categoria: str
    tipo: str
    linha: int
    parametros: list = field(default_factory=list)


@dataclass
class Escopo:
    numero: int
    descricao: str
    pai: object = None
    simbolos: list = field(default_factory=list)

    def buscar_local(self, nome):
        for simbolo in self.simbolos:
            if simbolo.nome == nome:
                return simbolo
        return None

    def buscar(self, nome):
        escopo = self
        while escopo is not None:
            encontrado = escopo.buscar_local(nome)
            if encontrado is not None:
                return encontrado
            escopo = escopo.pai
        return None


class AnalisadorSemantico:
    def __init__(self, arvore):
        self.arvore = arvore
        self.escopos = [Escopo(0, "global")]
        self.global_ = self.escopos[0]
        self.atual = self.global_
        self.funcao_atual = None
        self.tipo_retorno_atual = None
        self.linha_atual = 1
        self.coluna_atual = 1

    def erro(self, mensagem, linha=None, coluna=None):
        if linha is None:
            linha = self.linha_atual
        if coluna is None:
            coluna = self.coluna_atual
        raise ErroMPL("semantico", linha, coluna, mensagem)

    def marcar(self, no):
        if no is not None:
            self.linha_atual = getattr(no, "linha", self.linha_atual)
            self.coluna_atual = getattr(no, "coluna", 1)

    def abrir_escopo(self, descricao):
        novo = Escopo(len(self.escopos), descricao, self.atual)
        self.escopos.append(novo)
        self.atual = novo
        return novo

    def fechar_escopo(self):
        if self.atual.pai is not None:
            self.atual = self.atual.pai

    def declarar(self, simbolo):
        if self.atual.buscar_local(simbolo.nome) is not None:
            self.erro(
                f"nome '{simbolo.nome}' ja declarado neste escopo",
                simbolo.linha
            )
        self.atual.simbolos.append(simbolo)

    # Primeira passada: todas as funções ficam conhecidas antes
    # de qualquer corpo ser analisado (recursão direta e indireta).
    def coletar_funcoes(self):
        for funcao in self.arvore.funcoes:
            self.marcar(funcao)
            if self.global_.buscar_local(funcao.nome) is not None:
                self.erro(
                    f"funcao '{funcao.nome}' declarada mais de uma vez",
                    funcao.linha
                )
            self.global_.simbolos.append(Simbolo(
                funcao.nome,
                "funcao",
                funcao.tipo_retorno,
                funcao.linha,
                [p.tipo for p in funcao.parametros]
            ))

        principal = self.global_.buscar_local("principal")
        if principal is None:
            self.erro("funcao principal nao declarada", 1)
        if principal.tipo != "vazio" or principal.parametros:
            self.erro(
                "principal deve ser vazio e nao receber parametros",
                principal.linha
            )

    # Segunda passada: parâmetros e bloco da função são escopos distintos.
    def analisar_funcoes(self):
        for funcao in self.arvore.funcoes:
            self.marcar(funcao)
            self.funcao_atual = funcao
            self.tipo_retorno_atual = funcao.tipo_retorno

            self.abrir_escopo(f"funcao {funcao.nome}")
            for parametro in funcao.parametros:
                self.marcar(parametro)
                self.declarar(Simbolo(
                    parametro.nome, "parametro", parametro.tipo,
                    parametro.linha
                ))

            garante_retorno = self.analisar_bloco(funcao.bloco)
            if funcao.tipo_retorno != "vazio" and not garante_retorno:
                self.erro(
                    f"funcao '{funcao.nome}' pode terminar sem retornar valor",
                    funcao.linha
                )

            self.fechar_escopo()
            self.funcao_atual = None
            self.tipo_retorno_atual = None

    def analisar_bloco(self, bloco):
        self.abrir_escopo("bloco")
        garante_retorno = False

        for comando in bloco.comandos:
            self.marcar(comando)
            resultado = self.analisar_comando(comando)
            if resultado:
                garante_retorno = True

        self.fechar_escopo()
        return garante_retorno

    def analisar_comando(self, comando):
        if isinstance(comando, ast.Bloco):
            return self.analisar_bloco(comando)

        if isinstance(comando, ast.Declaracao):
            self.analisar_declaracao(comando)
            return False

        if isinstance(comando, ast.Atribuicao):
            self.analisar_atribuicao(comando)
            return False

        if isinstance(comando, ast.Escreva):
            tipo = self.tipo_expressao(comando.expressao)
            if tipo == "vazio":
                self.erro("nao e possivel escrever uma expressao vazia")
            return False

        if isinstance(comando, ast.Se):
            tipo = self.tipo_expressao(comando.cond)
            if tipo != "logico":
                self.erro("a condicao do se deve ser logica")

            retorna_entao = self.analisar_bloco(comando.bloco_entao)
            if comando.bloco_senao is None:
                return False
            retorna_senao = self.analisar_bloco(comando.bloco_senao)
            return retorna_entao and retorna_senao

        if isinstance(comando, ast.Enquanto):
            tipo = self.tipo_expressao(comando.cond)
            if tipo != "logico":
                self.erro("a condicao do enquanto deve ser logica")
            self.analisar_bloco(comando.bloco)
            return False

        if isinstance(comando, ast.Retorne):
            self.analisar_retorno(comando)
            return True

        if isinstance(comando, ast.Chamada):
            self.tipo_chamada(comando, como_comando=True)
            return False

        self.erro("comando sem tratamento semantico")

    def analisar_declaracao(self, no):
        self.marcar(no)
        simbolo = Simbolo(no.nome, "variavel", no.tipo, no.linha)
        self.declarar(simbolo)
        if no.expr is not None:
            tipo_expr = self.tipo_expressao(no.expr)
            if not self.compativel(no.tipo, tipo_expr):
                self.erro(
                    f"nao e possivel atribuir {tipo_expr} a variavel "
                    f"{no.nome} do tipo {no.tipo}", no.linha
                )

    def analisar_atribuicao(self, no):
        self.marcar(no)
        simbolo = self.atual.buscar(no.nome)
        if simbolo is None:
            self.erro(f"variavel '{no.nome}' nao declarada", no.linha)
        if simbolo.categoria == "funcao":
            self.erro(f"'{no.nome}' nao e uma variavel", no.linha)

        tipo_expr = self.tipo_expressao(no.expr)
        if not self.compativel(simbolo.tipo, tipo_expr):
            self.erro(f"tipo incompativel na atribuicao de '{no.nome}'", no.linha)

    def analisar_retorno(self, no):
        self.marcar(no)
        tipo_funcao = self.tipo_retorno_atual
        if no.expr is None:
            if tipo_funcao != "vazio":
                self.erro("funcao deve retornar um valor")
        else:
            if tipo_funcao == "vazio":
                self.erro("funcao vazio nao pode retornar um valor")
            tipo_expr = self.tipo_expressao(no.expr)
            if not self.compativel(tipo_funcao, tipo_expr):
                self.erro("tipo de retorno incompativel")

    @staticmethod
    def numerico(tipo):
        return tipo in ("inteiro", "real")

    @staticmethod
    def compativel(esperado, recebido):
        return esperado == recebido or (
            esperado == "real" and recebido == "inteiro"
        )

    def tipo_expressao(self, no):
        self.marcar(no)

        if isinstance(no, ast.Literal):
            return no.tipo

        if isinstance(no, ast.Variavel):
            simbolo = self.atual.buscar(no.nome)
            if simbolo is None:
                self.erro(f"variavel '{no.nome}' nao declarada")
            if simbolo.categoria == "funcao":
                self.erro(f"'{no.nome}' e uma funcao, nao uma variavel")
            return simbolo.tipo

        if isinstance(no, ast.Chamada):
            return self.tipo_chamada(no)

        if isinstance(no, ast.Unario):
            tipo = self.tipo_expressao(no.operando)
            if no.op == "nao":
                if tipo != "logico":
                    self.marcar(no)
                    self.erro("operador nao exige operando logico")
                return "logico"
            if no.op == "-":
                if not self.numerico(tipo):
                    self.marcar(no)
                    self.erro("menos unario exige operando numerico")
                return tipo

        if isinstance(no, ast.Binario):
            esquerda = self.tipo_expressao(no.esquerda)
            direita = self.tipo_expressao(no.direita)
            self.marcar(no)
            op = no.op

            if op in ("e", "ou"):
                if esquerda != "logico" or direita != "logico":
                    self.erro(f"operador '{op}' exige operandos logicos")
                return "logico"

            if op in ("==", "!="):
                if esquerda == direita or (
                    self.numerico(esquerda) and self.numerico(direita)
                ):
                    return "logico"
                self.erro(f"tipos incompativeis para operador '{op}'")

            if op in ("<", "<=", ">", ">="):
                if not self.numerico(esquerda) or not self.numerico(direita):
                    self.erro(f"operador '{op}' exige operandos numericos")
                return "logico"

            if op == "+":
                if esquerda == "texto" and direita == "texto":
                    return "texto"
                if self.numerico(esquerda) and self.numerico(direita):
                    return self.tipo_numerico(esquerda, direita)
                self.erro("operandos incompativeis para '+'")

            if op == "%":
                if esquerda != "inteiro" or direita != "inteiro":
                    self.erro("operador '%' exige dois inteiros")
                return "inteiro"

            if op in ("-", "*", "/"):
                if not self.numerico(esquerda) or not self.numerico(direita):
                    self.erro(f"operador '{op}' exige operandos numericos")
                return self.tipo_numerico(esquerda, direita)

            self.erro(f"operador desconhecido '{op}'")

        self.erro("expressao sem tratamento semantico")

    @staticmethod
    def tipo_numerico(esquerda, direita):
        if esquerda == "real" or direita == "real":
            return "real"
        return "inteiro"

    def tipo_chamada(self, no, como_comando=False):
        self.marcar(no)
        funcao = self.global_.buscar_local(no.nome)
        if funcao is None:
            self.erro(f"funcao '{no.nome}' nao declarada", no.linha)
        if funcao.categoria != "funcao":
            self.erro(f"'{no.nome}' nao e uma funcao", no.linha)
        if len(no.args) != len(funcao.parametros):
            self.erro(
                f"quantidade incorreta de argumentos na funcao '{no.nome}'",
                no.linha
            )

        for indice, argumento in enumerate(no.args):
            tipo_argumento = self.tipo_expressao(argumento)
            tipo_parametro = funcao.parametros[indice]
            if not self.compativel(tipo_parametro, tipo_argumento):
                self.erro(
                    f"tipo incorreto no argumento {indice + 1} "
                    f"da funcao '{no.nome}'", no.linha
                )

        if funcao.tipo == "vazio" and not como_comando:
            self.erro(
                f"funcao vazio '{no.nome}' nao pode ser usada em expressao",
                no.linha
            )
        return funcao.tipo

    def analisar(self):
        self.coletar_funcoes()
        self.analisar_funcoes()
        return self.escopos


def analisar(arvore):
    return AnalisadorSemantico(arvore).analisar()


def despejar(tabela):
    linhas = []
    for escopo in tabela:
        if escopo.numero == 0:
            linhas.append("escopo 0 global")
        else:
            linhas.append(
                f"escopo {escopo.numero} {escopo.descricao} "
                f"pai {escopo.pai.numero}"
            )

        for simbolo in escopo.simbolos:
            if simbolo.categoria == "funcao":
                parametros = ",".join(simbolo.parametros)
                linhas.append(
                    f"  {simbolo.nome}|funcao|{simbolo.tipo}"
                    f"({parametros})|{simbolo.linha}"
                )
            else:
                linhas.append(
                    f"  {simbolo.nome}|{simbolo.categoria}|"
                    f"{simbolo.tipo}|{simbolo.linha}"
                )
    return linhas
