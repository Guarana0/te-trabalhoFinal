document.addEventListener('DOMContentLoaded', () => {
    const areaGrafico = document.querySelector('[data-grafico]');
    const grafico = areaGrafico?.querySelector('svg');
    const dados = areaGrafico
        ? document.getElementById(areaGrafico.dataset.dados)
        : null;

    if (grafico && dados) {
        const periodos = JSON.parse(dados.textContent);
        const cor = areaGrafico.dataset.cor || '#ef4444';
        const criarElemento = (nome, atributos = {}) => {
            const elemento = document.createElementNS('http://www.w3.org/2000/svg', nome);
            Object.entries(atributos).forEach(([chave, valor]) => {
                elemento.setAttribute(chave, valor);
            });
            return elemento;
        };

        grafico.replaceChildren();

        if (periodos.every((periodo) => periodo.valor === 0)) {
            const mensagem = criarElemento('text', {
                x: 450,
                y: 155,
                'text-anchor': 'middle',
                class: 'chart-label',
            });
            mensagem.textContent = areaGrafico.dataset.vazio || 'Registre um lançamento para visualizar o gráfico.';
            grafico.append(mensagem);
        } else {
            const margem = { topo: 20, direita: 24, baixo: 42, esquerda: 64 };
            const largura = 900 - margem.esquerda - margem.direita;
            const altura = 300 - margem.topo - margem.baixo;
            const maiorValor = Math.max(...periodos.map((periodo) => periodo.valor), 1);
            const formatarValor = new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL',
                maximumFractionDigits: 0,
            });

            for (let linha = 0; linha <= 4; linha += 1) {
                const y = margem.topo + (altura * linha) / 4;
                grafico.append(criarElemento('line', {
                    x1: margem.esquerda,
                    x2: 900 - margem.direita,
                    y1: y,
                    y2: y,
                    class: 'chart-grid',
                }));
                const rotulo = criarElemento('text', {
                    x: margem.esquerda - 8,
                    y: y + 4,
                    'text-anchor': 'end',
                    class: 'chart-label',
                });
                rotulo.textContent = formatarValor.format(maiorValor * (4 - linha) / 4);
                grafico.append(rotulo);
            }

            const espaco = largura / periodos.length;
            const larguraBarra = Math.min(48, espaco * 0.58);
            periodos.forEach((periodo, indice) => {
                const alturaBarra = (periodo.valor / maiorValor) * (altura - 8);
                const x = margem.esquerda + indice * espaco + (espaco - larguraBarra) / 2;
                const y = margem.topo + altura - alturaBarra;
                const barra = criarElemento('rect', {
                    x,
                    y,
                    width: larguraBarra,
                    height: Math.max(alturaBarra, 1),
                    class: 'chart-bar',
                });
                barra.style.fill = cor;
                const dica = criarElemento('title');
                dica.textContent = `${periodo.rotulo}: ${formatarValor.format(periodo.valor)}`;
                barra.append(dica);
                grafico.append(barra);

                if (periodos.length <= 6 || indice % 2 === 0) {
                    const rotulo = criarElemento('text', {
                        x: x + larguraBarra / 2,
                        y: 280,
                        'text-anchor': 'middle',
                        class: 'chart-label',
                    });
                    rotulo.textContent = periodo.rotulo;
                    grafico.append(rotulo);
                }
            });
        }
    }

    if (document.querySelector('[data-abrir-modal="true"]')) {
        const formulario = document.querySelector('[data-abrir-modal="true"]');
        const modal = formulario?.closest('.modal');
        if (modal && window.bootstrap) {
            window.bootstrap.Modal.getOrCreateInstance(modal).show();
        }
    }
});
