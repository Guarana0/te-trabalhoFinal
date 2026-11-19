document.addEventListener('DOMContentLoaded', () => {
    const botoesTema = document.querySelectorAll('[data-botao-tema]');
    const temaSalvo = localStorage.getItem('tema');

    if (temaSalvo === 'escuro') {
        document.documentElement.dataset.tema = 'escuro';
    }

    const atualizarBotoesTema = () => {
        const temaEscuro = document.documentElement.dataset.tema === 'escuro';
        botoesTema.forEach((botao) => {
            const icone = botao.querySelector('[data-icone-tema]');

            if (icone) {
                icone.className = temaEscuro ? 'bi bi-sun-fill me-2' : 'bi bi-moon-stars-fill me-2';
            }
            botao.setAttribute('aria-checked', String(temaEscuro));
        });
    };

    atualizarBotoesTema();

    botoesTema.forEach((botao) => {
        botao.addEventListener('click', () => {
            const temaEscuro = document.documentElement.dataset.tema !== 'escuro';
            document.documentElement.dataset.tema = temaEscuro ? 'escuro' : 'claro';
            localStorage.setItem('tema', temaEscuro ? 'escuro' : 'claro');
            atualizarBotoesTema();
        });
    });
});
