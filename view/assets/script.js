document.addEventListener('DOMContentLoaded', () => {
    const page = document.body.dataset.page;

    if (page === 'dashboard') {
        const dashboardData = {
            '6m': {
                saldo: 'R$ 18.450',
                receitas: 'R$ 24.800',
                despesas: 'R$ 12.350',
                investimentos: 'R$ 9.200',
                chart: [42, 48, 55, 60, 62, 68]
            },
            '12m': {
                saldo: 'R$ 21.900',
                receitas: 'R$ 29.600',
                despesas: 'R$ 13.450',
                investimentos: 'R$ 11.800',
                chart: [35, 42, 48, 52, 60, 74]
            },
            '30d': {
                saldo: 'R$ 17.200',
                receitas: 'R$ 22.600',
                despesas: 'R$ 11.900',
                investimentos: 'R$ 8.700',
                chart: [46, 49, 53, 58, 62, 66]
            }
        };

        const rangeSelect = document.getElementById('dashboardRange');
        const chart = document.getElementById('dashboardChart');

        const setValue = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };

        const renderDashboardChart = (values) => {
            if (!chart) return;
            const w = 700;
            const h = 220;
            const pad = 20;
            const max = Math.max(...values) + 10;
            const points = values.map((v, i) => {
                const x = pad + (i * (w - pad * 2)) / (values.length - 1);
                const y = h - pad - ((v / max) * (h - pad * 2));
                return `${x},${y}`;
            }).join(' ');

            chart.innerHTML = `
                <svg viewBox="0 0 ${w} ${h}" width="100%" height="100%" preserveAspectRatio="none" aria-label="Gráfico financeiro">
                    <defs>
                        <linearGradient id="dashFill" x1="0" x2="0" y1="0" y2="1">
                            <stop offset="0%" stop-color="#2563eb" stop-opacity="0.30" />
                            <stop offset="100%" stop-color="#2563eb" stop-opacity="0.02" />
                        </linearGradient>
                    </defs>
                    <g stroke="#e2e8f0" stroke-width="1">
                        <line x1="20" y1="20" x2="680" y2="20" />
                        <line x1="20" y1="80" x2="680" y2="80" />
                        <line x1="20" y1="140" x2="680" y2="140" />
                        <line x1="20" y1="200" x2="680" y2="200" />
                    </g>
                    <polyline fill="none" stroke="#2563eb" stroke-width="3" points="${points}" />
                    <polygon points="20,200 ${points} 660,200" fill="url(#dashFill)" opacity="0.9" />
                </svg>
            `;
        };

        const updateDashboard = (period) => {
            const data = dashboardData[period];
            setValue('dashboardSaldo', data.saldo);
            setValue('dashboardReceitas', data.receitas);
            setValue('dashboardDespesas', data.despesas);
            setValue('dashboardInvestimentos', data.investimentos);
            renderDashboardChart(data.chart);
        };

        if (rangeSelect) {
            rangeSelect.addEventListener('change', (event) => {
                updateDashboard(event.target.value);
            });
        }

        updateDashboard('6m');
    }
});
