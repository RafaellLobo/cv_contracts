import os
import subprocess
import sys


def abrir_arquivo_sistema(caminho):
    if sys.platform == "win32":
        os.startfile(caminho)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", caminho])
    else:
        subprocess.Popen(["xdg-open", caminho])


def formatar_tamanho_legivel(tamanho):
    return f"{tamanho} B" if tamanho < 1024 else (
        f"{tamanho/1024:.1f} KB" if tamanho < 1024*1024 else
        f"{tamanho/(1024*1024):.1f} MB")


def listar_itens_visiveis(pasta):
    if not os.path.exists(pasta):
        return []
    return sorted([item for item in os.listdir(pasta) if not item.startswith('.')])


def contar_itens_visiveis(pasta):
    return len(listar_itens_visiveis(pasta))
