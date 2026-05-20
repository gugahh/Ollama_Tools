import re

def fc_extract_timestamps(subt_text):
    ''' 
    Recebe um texto contendo legendas, e extrai os indices + legendas para um array,
    substituindo-os por '###'.
    E util para diminuir o no de tokens de entrada / saida e assim acelerar a traducao via IA.
    '''
    # Initialize the array to store timestamps
    _subt_arr = []
    
    # Split the input text into lines
    lines = subt_text.split('\n')
    lines_to_remove = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if the current line is a timestamp
        if re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line):
            _timst = line
            # Get the subtitle number (position) which is one line above
            _posit = lines[i - 1].strip()
            
            # Store the position and timestamp as a tuple in the array
            _subt_arr.append((_posit, _timst))
            
            # Replace the timestamp with '###'
            lines[i] = '###'
            
            # Armazena a posicao da linha com o indice em lines_to_remove para a remocao, posterior.
            lines_to_remove.append(i-1)
        i += 1

    # Removendo as linhas que tem indices de legenda.
    # Isso tem que ser feito de tras para frente.
    lines_to_remove.reverse()
    for umaPosicao in lines_to_remove:
        removed_item = lines.pop(umaPosicao)
    
    # Join the processed lines back into a single string
    processed_text = '\n'.join(lines)
    
    return processed_text, _subt_arr


def fc_restore_timestamps(modded_text, arr_timestamps):
    ''' 
    Realiza a operacao inversa:
    Recebe um texto contendo legendas com marcadores do tipo ###, e uma lista de timestamps;
    Combina-os, substituindo os marcadores '###' pelo indice e timestamp da legenda.
    '''

    if not modded_text:
        raise ValueError("modded_text e obrigatorio.")
    
    if not arr_timestamps:
        raise ValueError("arr_timestamps e obrigatorio.")
    
    qt_posicoes_subst = modded_text.count('###')
    if (qt_posicoes_subst != len(arr_timestamps)):
        print('**** OPS! *****\nTemos um erro, mano\ns')
        print(f'modded_text:')
        print(modded_text)
        print(f'\narr_timestamps: \n{arr_timestamps}\n' )
        raise ValueError(f"Arrays tem tamanhos diferentes.\n- Qt de legendas: {qt_posicoes_subst} itens;\n - Qt de timestamps: {len(arr_timestamps)} itens.")

    # Split the input text into lines
    lines = modded_text.split('\n')
    
    idx_linha = 0
    idx_timestamps = 0

    while idx_linha < len(lines):
        line = lines[idx_linha].strip()
        
        # Check if the current line contains '###'
        if line == '###':
            _posit, _timst = arr_timestamps[idx_timestamps]
            
            # Replace '###' with the subtitle index, '\n' and srt timestamp
            lines[idx_linha] = _posit
            lines.insert(idx_linha + 1, _timst)
            idx_timestamps += 1     #Ja esta na posicao do proximo item.

        idx_linha += 1
    
    # Join the processed lines back into a single string
    restored_text = '\n'.join(lines)
    return restored_text


def short_test():
    print('Testando *fc_extract_timestamps*')
    sample_text = """
    1
    00:00:28,362 --> 00:00:30,598
    -Shh, shh, shh, shh, shh, shh.

    2
    00:00:50,018 --> 00:00:52,085
    -Is it morning?

    3
    00:00:52,185 --> 00:00:54,622
    -No, keep sleeping.
    """

    print(sample_text)
    print('-------------------------')
    _proc_text, _arr_sub = fc_extract_timestamps(sample_text)
    print(_proc_text)
    print('\n')
    print(_arr_sub)
    print('-------------------------\n')

    print('Testando *fc_restore_timestamps*')


    modded_text = """
###
-Shh, shh, shh, shh, shh, shh.

###
-Is it morning?

###
-No, keep sleeping.
    """

    print(modded_text)

    arr_timestamps = [
        ('1', '00:00:28,362 --> 00:00:30,598'),
        ('2', '00:00:50,018 --> 00:00:52,085'),
        ('3', '00:00:52,185 --> 00:00:54,622')
    ]

    restored_text = fc_restore_timestamps(modded_text, arr_timestamps)
    print("Restored Text:")
    print(restored_text)



if __name__ == "__main__":
    short_test()

