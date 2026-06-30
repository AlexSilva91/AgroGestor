from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.backups import executar_backup_config
from core.models import BackupConfig


class Command(BaseCommand):
    help = "Executa backups automáticos ativos conforme a frequência configurada."

    def handle(self, *args, **options):
        agora = timezone.now()
        total = 0
        for config in BackupConfig.objects.filter(ativo=True).select_related("farm"):
            if not _deve_executar(config, agora):
                continue
            execucao = executar_backup_config(config)
            total += 1
            self.stdout.write(f"{config.farm.nome}: {execucao.status} - {execucao.mensagem}")
        self.stdout.write(self.style.SUCCESS(f"Backups processados: {total}"))


def _deve_executar(config, agora):
    if config.hora_execucao and agora.time() < config.hora_execucao:
        return False
    if not config.ultima_execucao_em:
        return True

    delta = agora - config.ultima_execucao_em
    if config.frequencia == "DIARIO":
        return delta >= timedelta(days=1)
    if config.frequencia == "SEMANAL":
        return delta >= timedelta(days=7)
    if config.frequencia == "MENSAL":
        return delta >= timedelta(days=30)
    return False
