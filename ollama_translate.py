import ollama
import sys
import os
import math
import time
import includes_python.srt_preprocess_tools as sptools
import includes_python.srt_postprocess as srtpost

# Configuration
#MODEL = "gemma4:e4b" #Até o momento, o melhor
#MODEL = "qcwind/qwen3-8b-instruct-Q4-K-M:latest" #Mais lento que o Gemma... qualidade similar.
#MODEL = "phi4-mini" # Muito rapido, mas a qualidade e sofrivel. Bom para testes.
#MODEL = "gemma3:4b" 
MODEL = "gemma2:9b"  # Sugerido pela Gemini
MODEL = "translategemma:4b" 



SYSTEM_PROMPT_PADRAO = (
    "You are an expert subtitler. Translate the following movie dialogue into "
    "natural Brazilian Portuguese."
    "Use informal 'você' and ensure gender agreement based on context."
    "Keep the lines with ### marker unchanged, and never remove their carriage returns."
    "Do not create new instances of the ### marker."
    "The translated text will have the exact amount of ### markers then the original text."
)

SYSTEM_PROMPT_ALTERNATIVO = (
    "You are an expert subtitler. Translate the following movie dialogue into "
    "natural Brazilian Portuguese. Maintain the SRT formatting (timestamps and indices). "
    "Use informal 'você' and ensure gender agreement based on context."
)

def formata_interv_hh_mm_ss(a_time_diff):
    '''
        Formata um intervalo de tempo automaticamente no formato 14h12m14s ou 23:12s ou 24s,
        dependendo do tamanho do intervalo.
    '''
    hours = int(a_time_diff // 3600)
    minutes = int((a_time_diff % 3600) // 60)
    seconds = int(a_time_diff % 60)

    if (a_time_diff > 3600):    # Exibir hora, min, sec
        return f"{hours:02}h{minutes:02}m{seconds:02}s"
    elif (a_time_diff > 60):    # Exibir min, sec
        return f"{minutes:02}m{seconds:02}s"
    else:                       # Exibir apenas sec
        return f"{seconds:02}s"

def translate_srt_chunk(system_prompt, text_chunk):
    """Envia um bloco (chunk) de legendas SRT para o Ollama, para traducao."""
    response = ollama.chat(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"Translate this SRT block:\n\n{text_chunk}"}
        ],
        options={'temperature': 0.3} # Low temperature for consistency
    )
    return response['message']['content']

def process_subtitle(file_path, output_path, chunk_size=10):
    """Le o arquivo SRT, quebra em chunks de 'N' legendas, and envia para a traducao."""
    print('\nIniciando...')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by the double newline that separates SRT blocks
    subtitles = content.strip().split('\n\n')
    translated_content = []
    qt_blocos_reprocessados = 0

    total_chunks = math.ceil(len(subtitles) / chunk_size)
    print(f"\n\tModelo de IA utilizado: {MODEL}")
    print(f"\tQuantidade de legendas a traduzir: {len(subtitles)}")
    print(f"\tQuantidade de chunks: {total_chunks} (Prepare-se, é demorado!!)")

    start_total = time.time() # Horario do inicio de todas as operacoes

    for i in range(0, len(subtitles), chunk_size):
        current_chunk = i // chunk_size + 1

        chunk = "\n\n".join(subtitles[i : i + chunk_size])

        #Preprocessando o chunk: removendo timestamps para acelerar a traducao.
        #Eles serao re-inseridos, apos a traducao deste chunk.
        modded_text, arr_timestamps = sptools.fc_extract_timestamps(chunk)

        print(f"\n>> Traduzindo o chunk {current_chunk}/{total_chunks} ...\n")
        start_time = time.time()  # Armazenando a hora de inicio dessa iteracao

        '''
        # ---
        print('Imprimindo modded_text')
        print(modded_text)
        print('-----------------')
        print('Imprimindo arr_timestamps')
        print(arr_timestamps)
        print('-----------------')
        '''
        
        translated_chunk = translate_srt_chunk(SYSTEM_PROMPT_PADRAO, modded_text)

        # As vezes algum codigo maroto pode salvar erros de IA. Tipo repeticao de ### .
        # Vamos tentar acertar, antes de declarar que essa traducao vai causar erro ou nao.
        translated_chunk2 = srtpost.fc_remove_lixo_traducao(translated_chunk)

        # Verificando se a quantidade de ### eh igual a quantidade de timestamps,
        # apos a traducao, que eh quando acontece erro (eventualmente).
        # Se houver divergencia, a IA repetiu erradamente o ###, e temos que fazer
        # a traducao convencional (mais lenta), usando timestamps.
        traducao_valida = True if(translated_chunk2.count('###') == len(arr_timestamps)) else False

        if traducao_valida:
            '''
            print('Imprimindo translated_chunk pre tratamento')
            print('-----------------')
            print(translated_chunk)
            print('-----------------')

            print('Imprimindo translated_chunk - pos tratamento')
            print('-----------------')
            print(translated_chunk2)
            print('-----------------')
            '''
            #Restaurando os timestamps no texto ja traduzido
            restored_text = sptools.fc_restore_timestamps(translated_chunk2, arr_timestamps)

            print('> Resultado da traducao:\n')
            print(restored_text)
            print('-----------------')

            translated_content.append(restored_text)
        else: 
            # Fluxo alternativo: Sabe-se que essa traducao vai causar erro.
            # Vamos traduzir de novo esse chunk, e dessa vez vamos 
            # passar as legendas sem a substituicao de timestamps por ### 
            print('**** Atencao: Erro na contagem de (###). Reprocessando esse bloco!')
            translated_chunk = translate_srt_chunk(SYSTEM_PROMPT_ALTERNATIVO, chunk)
            print('> Resultado da traducao:\n')
            print(translated_chunk)
            print('-----------------')
            qt_blocos_reprocessados += 1
            translated_content.append(translated_chunk)
            
        end_time = time.time()  # Hora do fim dessa iteracao
        print(f'\n\t> Chunk processado em {formata_interv_hh_mm_ss(end_time - start_time)}.') # Tempo de processamento deste chunk

        tempo_tot_decorrido = time.time() - start_total;
        print(f'\t> Tempo total decorrido: {formata_interv_hh_mm_ss(tempo_tot_decorrido)}.') 

        if (current_chunk < total_chunks) :
            # Exibindo a estimativa de tempo restante
            # tempo restante = tempo medio de processamento * qt chunks restantes.
            tempo_estimado = (tempo_tot_decorrido / current_chunk) * (total_chunks - current_chunk)
            print(f'\t> Tempo estimado para a finalização: {formata_interv_hh_mm_ss(tempo_estimado)}')

    # Tudo deu certo? Gravando as legendas para o arquivo texto de saida.
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(translated_content))

    #Calculando o tempo total de todas as operacoes
    print(f'\n*** Quantidade de blocos reprocessados: {qt_blocos_reprocessados} ***')
    print(f'>>> Tradução finalizada em {formata_interv_hh_mm_ss(time.time() - start_total)}\n')

def main():
    # print('Entrou em main()')
    # sys.argv[0] is the script name itself.
    # We need at least one more argument (the filename).
    print('\n----------------------------------------')
    print('--    Iniciando o Ollama Translate    --')
    print('----------------------------------------\n')
    
    # 1. Check for missing command line parameter
    if len(sys.argv) == 1:
        print("Erro: Por favor forneça um nome de arquivo.")
        print(f"Utilização: python {sys.argv[0]} <nome_de_arquivo>")
        sys.exit(1) # Exit with non-zero status code indicating failure
        
    # Get the file path from the first command line argument
    file_path = sys.argv[1]
    print(f"\tNome arq de entrada:\t{file_path}")
    
    # 2. Check if the file exists
    if not os.path.exists(file_path):
        print(f"\n[ERRO] Arquivo nao encontrado: {file_path}")
        print("Por favor verifique que o arquivo existe e o caminho esta correto.")
        sys.exit(1) # Exit with non-zero status code
        
    # Nome do arquivo de saida: mesmo nome, so que com _pt-BR no final.
    nome_arq_saida = f"{file_path[:-4]}_pt-BR.srt"
    print(f"\tNome arq de saida:\t{nome_arq_saida}")

    chunk_size = 10 #Chunk size padrao. Funciona bem no Gemma.
    if (MODEL == "qcwind/qwen3-8b-instruct-Q4-K-M:latest"):
        chunk_size = 8 # Alterando o Chunk size no qwen3-8b; Tentando evitar travamento.
    print(f"\tChunk size:\t\t{chunk_size}")

    process_subtitle(file_path, nome_arq_saida , chunk_size) 

if __name__ == "__main__":
    #print('Chegou da linha de comando')
    main()
