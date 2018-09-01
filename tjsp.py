#!/usr/bin/env python
# coding=utf-8
import gevent.monkey

gevent.monkey.patch_all()
from bs4 import Tag, BeautifulSoup

import jus
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

from pymongo import MongoClient
from datetime import datetime

cliente = MongoClient()
banco = cliente['LegalHackers']
colecao = banco['tjsp']



processos = []
ssl._create_default_https_context = ssl._create_unverified_context

URL = "https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&dadosConsulta.localPesquisa.cdLocal=100&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&numeroDigitoAnoUnificado=1041100-50.2016&foroNumeroUnificado=0100&dadosConsulta.valorConsultaNuUnificado=%s&dadosConsulta.valorConsulta="
db = 'db'  # nome do diretorio
hashfilename = 'processos_hash.txt'


def get_processes(n_min=0, n_max=10000):
    return jus.process_generator(j=8, tr=26, o=53,n_min=n_min, n_max=n_max, ano=2014)


def clean_content(content):
    return re.sub(r'[\t\r\n]', '', "".join(content)).strip()


def clean_content_other(content):
    return re.sub(r';+', ';', re.sub(r'\t+|\r+|\n+', ';', "".join(content).strip()))


def get_movimentations(content_html):
    movs = []
    parsed_html = html.fromstring(content_html)
    soup = BeautifulSoup(content_html, features='lxml')
    table = soup.find('table', class_='secaoFormBody', id='')
    trs = [x for x in table.children if isinstance(x, Tag)]
    prev = ''
    for row in trs:
        # primeira coluna da nossa tabela data
        cols = row.find_all('td')
        data = prev = clean_content(cols[0].text) or prev
        # terceira coluna da nossa tabela conteudo da movimentacao
        movimentacao = clean_content(cols[1].text)
        movs.append(u"{}|{}\n".format(data, movimentacao))
        # return u"{}|{}\n".format(data, movimentacao) # cvs

    movimentacoes = parsed_html.xpath(
        '//*[@id="tabelaTodasMovimentacoes"]/tr')
    for row in movimentacoes:
        # primeira coluna da nossa tabela data
        data = clean_content(row.xpath('./td[1]/text()'))
        # terceira coluna da nossa tabela conteudo da movimentacao
        movimentacao = clean_content(row.xpath('./td[3]/text()'))
        extra = "".join(row.xpath('./td[3]/span/text()')).strip()
        text = u"{}|{}".format(data, movimentacao)
        if extra:
            text += f'|{clean_content_other(extra)}'
        movs.append(text+'\n')
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


def save_hashfile(numero, hash_):
    colecao.update_one(
        {'processo': numero},
        {
            '$set': {
                'hash': hash_, 
                'dt_modificacao': datetime.now()
            }
        },
        upsert=True
    )
    return True

def compare_hash(numero, hash_):
    hashcontent = hashlib.md5(hash_.encode('utf-8'))
    hashcontent = hashcontent.hexdigest()
    busca = colecao.find_one(
        {'processo': numero, 'hash': hashcontent}
    )
    if not busca:
        return save_hashfile(numero, hashcontent)
    return False


def update_process(process, sleep_=1.2):
    processo = process.strip()
    print("Coletando Movimentações: %s" % processo)
    conteudo = consulta_processo(processo)
    if conteudo:
        movimentacoes = get_movimentations(conteudo)
        if movimentacoes:
            _, last_mov = movimentacoes[0].split('|')
            if compare_hash(processo, last_mov):
                print("Gerando Hash: %s" % processo)
                colecao.update_one(
                    {'processo': processo},
                    {"$addToSet": {'movimentacoes': {"$each": movimentacoes}}},
                    upsert=True
                )
    time.sleep(sleep_)


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def asynchronous(chunk=10):
    processos = get_processes()
    for dataprocesses in chunks(processos, chunk):
        threads = []
        for processo in dataprocesses:
            threads.append(gevent.spawn(update_process, processo))
        gevent.joinall(threads)


if __name__ == '__main__':
    time.sleep(2)
    try:
        print("\n*** Checando a cada 5333min ***\n\n")
        while True:
            asynchronous()
            time.sleep(300)
    except KeyboardInterrupt:
        sys.exit(1)
