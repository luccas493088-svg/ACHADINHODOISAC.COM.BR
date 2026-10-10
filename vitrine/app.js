/* Vitrine Isac Achadinhos — lê produtos dos JSONs locais.
 * Dry-run: esta página NUNCA chama APIs externas por conta própria.
 * Saídas externas só acontecem por clique do visitante (oferta,
 * compartilhar, seguir) ou via Meta Pixel, que vem DESLIGADO por padrão.
 */
"use strict";

const LOJAS = ["Amazon", "Mercado Livre", "Monetizze"];

const estado = {
    loja: "Todas",
    ordem: "chegada",
    produtos: [],
    sociais: { instagram: "", facebook: "" },
    config: { destaque_quantidade: 3, por_loja_quantidade: 3 },
};

async function carregarJson(arquivo) {
    const resposta = await fetch(arquivo, { cache: "no-store" });
    if (!resposta.ok) {
        throw new Error(`Falha ao ler ${arquivo}: ${resposta.status}`);
    }
    return resposta.json();
}

const MENSAGEM_VAZIO = "Em breve novas ofertas";

async function carregarProdutos() {
    // Fonte primária: banco via API. Fallback: JSON local (demonstração).
    try {
        const resposta = await fetch("/api/vitrine/produtos?limite=100", {
            cache: "no-store",
        });
        if (!resposta.ok) {
            throw new Error(`API: ${resposta.status}`);
        }
        const dados = await resposta.json();
        if (Array.isArray(dados)) {
            return dados;
        }
        throw new Error("API sem lista");
    } catch (erroApi) {
        const dados = await carregarJson("links_afiliados.json");
        if (Array.isArray(dados.produtos)) {
            return dados.produtos;
        }
        throw erroApi;
    }
}

function mensagemVazio() {
    const aviso = document.createElement("p");
    aviso.className = "vazio";
    aviso.textContent = MENSAGEM_VAZIO;
    return aviso;
}

function formatarPreco(valor) {
    return Number(valor).toLocaleString("pt-BR", {
        style: "currency",
        currency: estado.config.moeda || "BRL",
    });
}

function ordenar(produtos, ordem) {
    const lista = [...produtos];
    if (ordem === "baratos") {
        lista.sort((a, b) => a.preco - b.preco);
    } else if (ordem === "caros") {
        lista.sort((a, b) => b.preco - a.preco);
    } else {
        lista.sort((a, b) => String(a.data_cadastro).localeCompare(String(b.data_cadastro)));
    }
    return lista;
}

function fotoProduto(produto) {
    if (produto.imagem) {
        const img = document.createElement("img");
        img.className = "cartao-foto";
        img.src = produto.imagem;
        img.alt = produto.nome;
        img.loading = "lazy";
        return img;
    }
    const vazio = document.createElement("div");
    vazio.className = "cartao-foto cartao-foto--vazia";
    vazio.textContent = "Foto em breve";
    return vazio;
}

function cartaoProduto(produto) {
    const artigo = document.createElement("article");
    artigo.className = "cartao";
    artigo.appendChild(fotoProduto(produto));

    const corpo = document.createElement("div");
    corpo.className = "cartao-corpo";

    const loja = document.createElement("span");
    loja.className = "cartao-loja";
    loja.textContent = produto.loja;
    corpo.appendChild(loja);

    const nome = document.createElement("h3");
    nome.className = "cartao-nome";
    nome.textContent = produto.nome;
    corpo.appendChild(nome);

    const preco = document.createElement("div");
    preco.className = "cartao-preco";
    preco.textContent = formatarPreco(produto.preco);
    corpo.appendChild(preco);

    const botao = document.createElement("a");
    botao.className = "btn-oferta";
    botao.textContent = "Ver oferta";
    botao.href = produto.link_afiliado || "#";
    botao.target = "_blank";
    botao.rel = "nofollow sponsored noopener";
    corpo.appendChild(botao);

    const compartilhar = document.createElement("div");
    compartilhar.className = "compartilhar";
    const texto = encodeURIComponent(`${produto.nome} — ${formatarPreco(produto.preco)}`);
    const link = encodeURIComponent(produto.link_afiliado || window.location.href);

    const face = document.createElement("a");
    face.textContent = "Compartilhar (Facebook)";
    face.href = `https://www.facebook.com/sharer/sharer.php?u=${link}`;
    face.target = "_blank";
    face.rel = "noopener";
    compartilhar.appendChild(face);

    const whats = document.createElement("a");
    whats.textContent = "Compartilhar (WhatsApp)";
    whats.href = `https://wa.me/?text=${texto}%20${link}`;
    whats.target = "_blank";
    whats.rel = "noopener";
    compartilhar.appendChild(whats);

    corpo.appendChild(compartilhar);
    artigo.appendChild(corpo);
    return artigo;
}

function botaoSocial(rede, url) {
    const a = document.createElement("a");
    a.className = "btn-social";
    a.textContent = rede === "instagram" ? "Siga no Instagram" : "Siga no Facebook";
    if (url) {
        a.href = url;
        a.target = "_blank";
        a.rel = "noopener";
    } else {
        a.href = "#";
        a.setAttribute("aria-disabled", "true");
        a.title = "Link em breve";
    }
    return a;
}

function renderizarSociais() {
    for (const id of ["social-topo", "social-rodape"]) {
        const nav = document.getElementById(id);
        nav.replaceChildren(
            botaoSocial("instagram", estado.sociais.instagram),
            botaoSocial("facebook", estado.sociais.facebook),
        );
    }
}

function renderizarMenu() {
    const ul = document.getElementById("menu-lojas");
    ul.replaceChildren();
    for (const nome of ["Todas", ...LOJAS]) {
        const li = document.createElement("li");
        const botao = document.createElement("button");
        botao.textContent = nome;
        if (nome === estado.loja) {
            botao.classList.add("ativo");
        }
        botao.addEventListener("click", () => {
            estado.loja = nome;
            renderizar();
        });
        li.appendChild(botao);
        ul.appendChild(li);
    }
}

function renderizar() {
    renderizarMenu();

    const base = estado.loja === "Todas"
        ? estado.produtos
        : estado.produtos.filter((p) => p.loja === estado.loja);

    // Vitrine principal: sempre os mais baratos do recorte atual.
    const destaque = [...base]
        .sort((a, b) => a.preco - b.preco)
        .slice(0, estado.config.destaque_quantidade);
    const gradeDestaque = document.getElementById("grade-destaque");
    if (destaque.length === 0) {
        gradeDestaque.replaceChildren(mensagemVazio());
    } else {
        gradeDestaque.replaceChildren(...destaque.map(cartaoProduto));
    }

    // Abaixo do destaque: 3 primeiros de cada loja (ordem do seletor).
    const area = document.getElementById("secoes-lojas");
    area.replaceChildren();
    if (estado.produtos.length === 0) {
        area.appendChild(mensagemVazio());
        return;
    }
    const lojas = estado.loja === "Todas" ? LOJAS : [estado.loja];
    for (const nome of lojas) {
        const itens = ordenar(
            estado.produtos.filter((p) => p.loja === nome),
            estado.ordem,
        ).slice(0, estado.config.por_loja_quantidade);
        if (itens.length === 0) {
            continue;
        }
        const secao = document.createElement("section");
        secao.className = "secao-loja";
        const titulo = document.createElement("h2");
        titulo.textContent = nome;
        secao.appendChild(titulo);
        const grade = document.createElement("div");
        grade.className = "grade";
        grade.replaceChildren(...itens.map(cartaoProduto));
        secao.appendChild(grade);
        area.appendChild(secao);
    }
}

function prepararPixel(config) {
    // DESLIGADO por padrão: só injeta o Pixel com flag + ID preenchidos.
    if (!config.meta_pixel_enabled || !config.meta_pixel_id) {
        return;
    }
    const script = document.createElement("script");
    script.async = true;
    script.src = "https://connect.facebook.net/en_US/fbevents.js";
    document.head.appendChild(script);
}

async function iniciar() {
    const [produtos, sociais, config] = await Promise.all([
        carregarProdutos(),
        carregarJson("redes_sociais.json"),
        carregarJson("configuracao.json"),
    ]);
    estado.produtos = produtos;
    estado.sociais = { instagram: sociais.instagram || "", facebook: sociais.facebook || "" };
    estado.config = { ...estado.config, ...config };

    document.getElementById("seletor-ordem").addEventListener("change", (evento) => {
        estado.ordem = evento.target.value;
        renderizar();
    });

    renderizarSociais();
    renderizar();
    prepararPixel(config);
}

iniciar().catch((erro) => {
    document.getElementById("secoes-lojas").textContent =
        `Não foi possível carregar a vitrine: ${erro.message}`;
});
