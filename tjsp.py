#!/usr/bin/env python
# coding=utf-8
import gevent.monkey

gevent.monkey.patch_all()

from jus import jus_gen
import sys
import time
import gevent
import os
import io
import re
import ssl
import socket
import hashlib
from lxml import html
from urllib.request import urlopen
from urllib.error import HTTPError, URLError


processos = []
ssl._create_default_https_context = ssl._create_unverified_context

URL = "https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&dadosConsulta.localPesquisa.cdLocal=100&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&numeroDigitoAnoUnificado=1041100-50.2016&foroNumeroUnificado=0100&dadosConsulta.valorConsultaNuUnificado=%s&dadosConsulta.valorConsulta="
db = 'db'  # nome do diretorio
hashfilename = 'processos_hash.txt'


def get_processes(filename='processos_tjsp_1.txt'):
    return jus_gen(j=8, tr=26, o=53, n_max=5, ano=2015)


def clean_content(content):
    return re.sub(r'[\t\r\n]', '', "".join(content)).strip()


def get_movimentations(content_html):
    movs = []
    movimentacoes = html.fromstring(content_html).xpath(
        '//*[@id="tabelaTodasMovimentacoes"]/tr')
    for row in movimentacoes:
        # primeira coluna da nossa tabela data
        data = clean_content(row.xpath('./td[1]/text()'))
        # terceira coluna da nossa tabela conteudo da movimentacao
        movimentacao = clean_content(row.xpath('./td[3]/text()'))
        movs.append(u"{}|{}\n".format(data, movimentacao))
        # return u"{}|{}\n".format(data, movimentacao) # cvs
    return movs


def consulta_processo(numero, timeout=10):
    try:
        resp = urlopen(URL % numero, timeout=timeout)
    except HTTPError as e:
        if e.code == 404:
            print(u"Processo: %s não existe." % (numero))
            return None
    except socket.timeout:
        print("Excedeu o tempo limite para o processo: %s" % (numero))
        return False
    except URLError as e:
        print(e)
        print("Error na captura do processo: %s." % (numero))
        return False
    else:
        return resp.read()


if not os.path.exists(db):
    os.makedirs(db)


def save_content(numero, content):
    with io.open(os.path.join(db, numero), 'a', encoding='utf8') as f:
        f.write(content)


def save_hashfile(numero, hash, position, append=False):
    if position == 0:
        with io.open(hashfilename, 'w', encoding='utf8') as f:
            f.write(u"{}|{}\n".format(numero, hash))
            return True

    with io.open(hashfilename, 'r', encoding='utf8') as f:
        contents = f.readlines()

        if not append:
            contents[position] = u"{}|{}\n".format(numero, hash)
        else:
            contents.append(u"{}|{}\n".format(numero, hash))

    with io.open(hashfilename, 'w', encoding='utf8') as f:
        f.write(u"".join(contents))
        return True


def compare_hash(numero, content):
    hashcontent = hashlib.md5(content.encode('utf-8'))
    status = False
    last = -1
    if not os.path.exists(hashfilename):
        return save_hashfile(numero, hashcontent.hexdigest(), 0)

    with io.open(hashfilename, 'r', encoding='utf8') as f:
        contents = f.readlines()

    for index, row in enumerate(contents):
        num, hashmov = row.split('|')
        last = index
        if num == numero:
            if hashcontent.hexdigest() == str(hashmov.strip()):
                return False
            else:
                print(u"Nova movimentação para o processo: %s posicao: %d" % (numero, index))
                return save_hashfile(numero, hashcontent.hexdigest(), index)

    if status == False:
        return save_hashfile(numero, hashcontent.hexdigest(), -1, True)


def main():
    if processos:
        for processo in processos:
            processo = processo.strip()
            print(u"Coletando Movimentações: %s" % processo)
            conteudo = consulta_processo(processo)
            if conteudo:
                movimentacoes = get_movimentations(conteudo)
                if movimentacoes:
                    _, last_mov = movimentacoes[0].split('|')
                    if compare_hash(processo, last_mov):
                        print("Gerando Hash: %s" % processo)
                        for mov in movimentacoes:
                            save_content(processo, mov)

    else:
        print(u"Não existe processos")


def update_process(process, sleep=1.2):
    processo = process.strip()
    print("Coletando Movimentações: %s" % processo)
    conteudo = consulta_processo(processo)
    if conteudo:
        movimentacoes = get_movimentations(conteudo)
        if movimentacoes:
            _, last_mov = movimentacoes[0].split('|')
            if compare_hash(processo, last_mov):
                print("Gerando Hash: %s" % processo)
                for mov in movimentacoes:
                    save_content(processo, mov)
                # notification(msg=processo)
    time.sleep(sleep)


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def asynchronous(chunk=2):
    processos = get_processes()
    for dataprocesses in chunks(processos, chunk):
        threads = []
        for processo in dataprocesses:
            threads.append(gevent.spawn(update_process, processo))
        gevent.joinall(threads)


if __name__ == '__main__':
    time.sleep(2)
    try:
        print("\n*** Checando a cada 5min ***\n\n")
        while True:
            asynchronous()
            time.sleep(300)
    except KeyboardInterrupt:
        sys.exit(1)
