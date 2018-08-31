def process_generator(j, tr, o, n_min=0, n_max=9999999, ano=2018):
    # Ano - Ano do ajuizamento do Processo
    # J - Órgão ou Segmento do Poder Judiciário
    # TR - Tribunal do respectivo Segmento do Poder Judiciário
    # O - Unidade de origem do Processo
    return_list = []
    for n in range(n_min, n_max + 1):
        numero = int(f'{n:07}{ano:04}{j:01}{tr:02}{o:04}')
        dd = 98 - (numero * 100 % 97)
        return_list.append(
            f'{n:07}-{dd:02}.{ano:04}.{j:01}.{tr:02}.{o:04}'
        )
    return return_list
