def jus_gen(j, tr, o, n_max, ano=2018):
    # Ano - Ano do ajuizamento do Processo
    # J - Órgão ou Segmento do Poder Judiciário
    # TR - Tribunal do respectivo Segmento do Poder Judiciário
    # O - Unidade de origem do Processo
    return_list = []
    for n in range(0, n_max + 1):
        numero = int(f'{n:07}{ano:04}{j:01}{tr:02}{o:04}')
        dd = 98 - (numero * 100 % 97)
        return_list.append(
            f'{n:07}-{dd:02}.{ano:04}.{j:01}.{tr:02}.{o:04}'
        )
    return return_list


numeros_validos = jus_gen(j=8, tr=26, o=53, n_max=5, ano=2015)
print(numeros_validos)
