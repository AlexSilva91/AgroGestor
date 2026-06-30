(function () {
    const colors = ['#287052', '#39758f', '#b58b18', '#5fa884', '#b6483f', '#738178', '#8a6a3f', '#4d7c8a'];

    document.addEventListener('DOMContentLoaded', carregarMetricasDashboard);

    function currency(value) {
        return Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }

    function number(value) {
        return Number(value || 0).toLocaleString('pt-BR');
    }

    async function carregarMetricasDashboard() {
        if (!document.getElementById('chartPlantelCultura')) return;
        try {
            const response = await fetch('/api/dashboard/metricas/');
            const data = await response.json();
            if (!response.ok || data.success === false) throw new Error(data.error || 'Erro ao carregar métricas.');

            document.getElementById('dashboardMetricScope').textContent = `${data.scope} - métricas operacionais, produtivas e financeiras.`;
            document.getElementById('kpiPlanteisAtivos').textContent = number(data.cards.planteis_ativos);
            document.getElementById('kpiAnimaisAtuais').textContent = number(data.cards.animais_atual);
            document.getElementById('kpiOvosTotal').textContent = number(data.cards.ovos_total);
            document.getElementById('kpiReceita').textContent = currency(data.cards.receita);
            document.getElementById('kpiCusto').textContent = currency(data.cards.custo);
            document.getElementById('kpiResultado').textContent = currency(data.cards.resultado);
            document.getElementById('kpiOcorrenciasAbertas').textContent = number(data.cards.ocorrencias_abertas);
            document.getElementById('kpiMortalidade').textContent = number(data.cards.mortalidade);
            document.getElementById('kpiNatalidade').textContent = number(data.cards.natalidade);

            drawBars('chartPlantelCultura', data.charts.plantel_por_cultura, { horizontal: true });
            drawBars('chartPlantelStatus', data.charts.plantel_por_status, { horizontal: true });
            drawLine('chartProducaoOvos', data.charts.producao_ovos_14_dias);
            drawBars('chartFinanceiroPlantel', data.charts.financeiro_por_plantel, { horizontal: false, money: true });
            drawLine('chartSanidadeMes', data.charts.sanidade_por_mes);
            drawBars('chartSanidadePlantel', data.charts.sanidade_por_plantel, { horizontal: true });
            drawGroupedBars('chartMortalidadeNatalidade', data.charts.mortalidade_vs_natalidade);
        } catch (error) {
            console.warn(error.message);
        }
    }

    function setup(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        const rect = canvas.getBoundingClientRect();
        const ratio = window.devicePixelRatio || 1;
        canvas.width = Math.max(320, rect.width) * ratio;
        canvas.height = (Number(canvas.getAttribute('height')) || 220) * ratio;
        const ctx = canvas.getContext('2d');
        ctx.scale(ratio, ratio);
        return { canvas, ctx, width: canvas.width / ratio, height: canvas.height / ratio };
    }

    function empty(ctx, width, height) {
        ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--text-muted') || '#75857b';
        ctx.font = '13px Segoe UI, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Sem dados para exibir', width / 2, height / 2);
    }

    function drawBars(canvasId, rows, options = {}) {
        const chart = setup(canvasId);
        if (!chart) return;
        const { ctx, width, height } = chart;
        ctx.clearRect(0, 0, width, height);
        rows = (rows || []).filter(row => Number(row.value) > 0);
        if (!rows.length) return empty(ctx, width, height);

        const max = Math.max(...rows.map(row => Number(row.value)));
        const pad = 18;
        ctx.font = '12px Segoe UI, sans-serif';
        ctx.textBaseline = 'middle';

        if (options.horizontal) {
            const rowHeight = Math.min(34, (height - pad * 2) / rows.length);
            rows.forEach((row, index) => {
                const y = pad + index * rowHeight;
                const labelWidth = Math.min(120, width * 0.34);
                const barWidth = (width - labelWidth - 70) * (Number(row.value) / max);
                ctx.fillStyle = '#52665b';
                ctx.textAlign = 'left';
                ctx.fillText(shortLabel(row.label, 18), pad, y + rowHeight / 2);
                ctx.fillStyle = colors[index % colors.length];
                roundRect(ctx, labelWidth, y + 6, Math.max(4, barWidth), rowHeight - 12, 6);
                ctx.fill();
                ctx.fillStyle = '#193227';
                ctx.textAlign = 'left';
                ctx.fillText(options.money ? currency(row.value) : number(row.value), labelWidth + barWidth + 8, y + rowHeight / 2);
            });
            return;
        }

        const chartBottom = height - 32;
        const chartTop = 16;
        const barGap = 10;
        const barWidth = Math.max(18, (width - pad * 2 - barGap * (rows.length - 1)) / rows.length);
        rows.forEach((row, index) => {
            const x = pad + index * (barWidth + barGap);
            const barHeight = (chartBottom - chartTop) * (Number(row.value) / max);
            ctx.fillStyle = colors[index % colors.length];
            roundRect(ctx, x, chartBottom - barHeight, barWidth, barHeight, 6);
            ctx.fill();
            ctx.fillStyle = '#52665b';
            ctx.textAlign = 'center';
            ctx.fillText(shortLabel(row.label, 10), x + barWidth / 2, height - 13);
        });
    }

    function drawLine(canvasId, rows) {
        const chart = setup(canvasId);
        if (!chart) return;
        const { ctx, width, height } = chart;
        ctx.clearRect(0, 0, width, height);
        rows = rows || [];
        if (!rows.length) return empty(ctx, width, height);

        const max = Math.max(1, ...rows.map(row => Number(row.value)));
        const left = 36;
        const right = 16;
        const top = 18;
        const bottom = height - 30;
        const step = (width - left - right) / Math.max(1, rows.length - 1);

        ctx.strokeStyle = 'rgba(40, 112, 82, 0.18)';
        ctx.lineWidth = 1;
        for (let i = 0; i < 4; i++) {
            const y = top + ((bottom - top) / 3) * i;
            ctx.beginPath();
            ctx.moveTo(left, y);
            ctx.lineTo(width - right, y);
            ctx.stroke();
        }

        ctx.strokeStyle = '#287052';
        ctx.lineWidth = 3;
        ctx.beginPath();
        rows.forEach((row, index) => {
            const x = left + index * step;
            const y = bottom - ((bottom - top) * (Number(row.value) / max));
            if (index === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();

        ctx.fillStyle = '#39758f';
        rows.forEach((row, index) => {
            const x = left + index * step;
            const y = bottom - ((bottom - top) * (Number(row.value) / max));
            ctx.beginPath();
            ctx.arc(x, y, 3.5, 0, Math.PI * 2);
            ctx.fill();
            if (index % 2 === 0 || rows.length <= 8) {
                ctx.fillStyle = '#52665b';
                ctx.font = '11px Segoe UI, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(row.label, x, height - 10);
                ctx.fillStyle = '#39758f';
            }
        });
    }

    function drawGroupedBars(canvasId, rows) {
        const chart = setup(canvasId);
        if (!chart) return;
        const { ctx, width, height } = chart;
        ctx.clearRect(0, 0, width, height);
        rows = rows || [];
        const max = Math.max(1, ...rows.flatMap(row => [Number(row.mortalidade || 0), Number(row.natalidade || 0)]));
        if (!rows.some(row => Number(row.mortalidade || 0) || Number(row.natalidade || 0))) {
            return empty(ctx, width, height);
        }

        const left = 24;
        const right = 16;
        const bottom = height - 30;
        const top = 20;
        const groupWidth = (width - left - right) / rows.length;
        const barWidth = Math.max(8, Math.min(18, groupWidth / 4));

        rows.forEach((row, index) => {
            const center = left + groupWidth * index + groupWidth / 2;
            const mortHeight = (bottom - top) * (Number(row.mortalidade || 0) / max);
            const natHeight = (bottom - top) * (Number(row.natalidade || 0) / max);

            ctx.fillStyle = '#b6483f';
            roundRect(ctx, center - barWidth - 2, bottom - mortHeight, barWidth, mortHeight, 5);
            ctx.fill();
            ctx.fillStyle = '#287052';
            roundRect(ctx, center + 2, bottom - natHeight, barWidth, natHeight, 5);
            ctx.fill();

            ctx.fillStyle = '#52665b';
            ctx.font = '11px Segoe UI, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(row.label, center, height - 10);
        });

        ctx.font = '12px Segoe UI, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillStyle = '#b6483f';
        ctx.fillText('Mortalidade', left, 10);
        ctx.fillStyle = '#287052';
        ctx.fillText('Natalidade', left + 92, 10);
    }

    function shortLabel(label, size) {
        label = String(label || '-');
        return label.length > size ? `${label.slice(0, size - 1)}...` : label;
    }

    function roundRect(ctx, x, y, width, height, radius) {
        const r = Math.min(radius, width / 2, height / 2);
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.arcTo(x + width, y, x + width, y + height, r);
        ctx.arcTo(x + width, y + height, x, y + height, r);
        ctx.arcTo(x, y + height, x, y, r);
        ctx.arcTo(x, y, x + width, y, r);
        ctx.closePath();
    }
})();
