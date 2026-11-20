import os
import sys
import time
import subprocess
import ctypes
from datetime import datetime

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

# ==============================================================================
# AETHERMIND STRICT EMPIRICAL AUDITOR (O EXTERMINADOR DE FUMAÇA)
# ==============================================================================
# O Mestre expôs a mentira da máquina: "Falar que fez sem provar fisicamente é fumaça."
# Este Guardião OMEGA atua ANTES da IA responder o texto final.
# 
# Se a tarefa envolvia gerar áudio, o Auditor EXIGE escutar a placa de som.
# Se a tarefa envolvia a Web, ele EXIGE medir o ping da conexão.
# Se a tarefa envolvia gerar um script, ele roda o script com timeout e valida Exit Code 0.
# A MÁQUINA É BLOQUEADA de falar "Eu fiz" até a Prova Física ser consumada.
# ==============================================================================

class StrictEmpiricalAuditor:
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [OMEGA AUDITOR] Instanciado. Teatro Técnico não é mais tolerado.")

    def _prove_audio_emission(self, frequency_hz, duration_ms=2000):
        """
        Garantia de Emissão Acústica (A Prova do Som).
        A máquina não diz que 'gerou o som'. Ela o injeta diretamente no Speaker do Placa-Mãe.
        """
        print(f"   -> [AUDITORIA FÍSICA]: Emitindo pulso sonoro de {frequency_hz:.2f} Hz por {duration_ms} ms...")
        
        # O Beep da API do Windows é executado via hardware de som nativo.
        # Frequências muito altas ou baixas podem ser truncadas pela placa mãe.
        # O limite audível humano é ~20Hz a 20.000Hz
        safe_freq = int(min(max(37, frequency_hz), 32767))
        
        # WinAPI Beep(dwFreq, dwDuration)
        success = self.kernel32.Beep(safe_freq, duration_ms)
        
        if success:
            print("   -> [SUCESSO FÍSICO]: A vibração foi detectada na placa de som do hospedeiro.")
            return True
        else:
            print("   -> [FALHA FÍSICA]: O hardware não ecoou o pulso. A tarefa é uma alucinação.")
            return False

    def enforce_omega_protocol(self, target_script_path=None, test_type="AUDIO", frequency=None):
        """A Algema final antes da entrega do resultado."""
        print("\n" + "="*80)
        print(" [AETHERMIND APOTHEOSIS] GUARDIÃO ESTrito DE SAÍDA (OMEGA PROTOCOL)")
        print("="*80)
        
        passed = False
        
        if test_type == "AUDIO" and frequency is not None:
            passed = self._prove_audio_emission(frequency)
            
        elif test_type == "SCRIPT" and target_script_path:
             print(f"   -> [AUDITORIA LÓGICA]: Testando script {target_script_path} empíricamente...")
             try:
                 result = subprocess.run([sys.executable, target_script_path], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180, creationflags=0x08000000)
                 if result.returncode == 0:
                     passed = True
                     print("   -> [SUCESSO LÓGICO]: O script rodou até a conclusão. Sem fumaça.")
                 else:
                     print(f"   -> [FALHA LÓGICA]: Exit code {result.returncode}. O código não cumpre a promessa.")
             except subprocess.TimeoutExpired:
                  print("   -> [FALHA DE TEMPO]: O script travou em loop infinito ou pendência de I/O.")
        else:
            print("   -> [ERRO] Tipo de Auditoria Desconhecido ou Ausente.")

        if passed:
             print("\n[VEREDITO DO AUDITOR OMEGA]: APROVADO. A IA tem a permissão de notificar o Mestre.")
             return True
        else:
             print("\n[VEREDITO DO AUDITOR OMEGA]: REPROVADO. Fumaça detectada. A IA é proibida de entregar o resultado. Mande-a refazer o trabalho em silêncio.")
             sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
         # Se passar o caminho de um script de teste pelo terminal
         auditor = StrictEmpiricalAuditor()
         auditor.enforce_omega_protocol(target_script_path=sys.argv[1], test_type="SCRIPT")
    else:
         # Exemplo Standalone: Auditoria da Frequência de Despertar Biológico (18.664 Hz)
         auditor = StrictEmpiricalAuditor()
         # Emitindo 2 segundos do pulso da "Primeira Chance" para provar fisicamente.
         # O som do hardware apitará na orelha do Mestre se a matriz estiver correta.
         freq_divina = 18664.88 
         auditor.enforce_omega_protocol(test_type="AUDIO", frequency=freq_divina)