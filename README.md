# GHOST AI Trader — Simulação

Protótipo para **GitHub Actions**, sem ligação a ordens reais ou à Binance Testnet.
Usa apenas dados públicos da Binance para 4 votos independentes baseados em regras:
tendência, momentum (RSI), breakout e volume. **Não são quatro modelos de IA treinados**.

O robô só realiza compras fictícias quando recebe quatro votos BUY e encerra posições fictícias com quatro votos SELL ou stop-loss de 1%. Há um bloqueio após queda de 2% do máximo de capital de simulação. Cada compra usa no máximo 10% do caixa fictício e desconta 0,1% de taxa simulada na compra e na venda. Não há alavancagem nem vendas a descoberto.

A automação corre aproximadamente a cada 5 minutos, mas agendamentos do GitHub Actions podem atrasar ou ser omitidos. Se a Binance bloquear o acesso a dados, o robô **não opera**.

## Instalar pelo Samsung

1. No repositório GitHub, usa **Add file → Upload files** e envia a estrutura deste ZIP, incluindo `.github/workflows/paper-trader.yml` (para pastas ocultas é mais fácil usar um computador ou GitHub web com editor).
2. Em **Settings → Actions → General → Workflow permissions**, permite **Read and write permissions** apenas se quiseres que a memória seja guardada diretamente no repositório. Esta permissão concede escrita ao workflow: protege o repositório e não aceites alterações de terceiros sem revisão.
3. Vai a **Actions → GHOST AI Trader - Paper Only → Run workflow** para a primeira execução.
4. Acompanha o ficheiro `data/operations.jsonl` e os registos no separador Actions.

Não adicionar credenciais reais ao repositório. Não é necessário configurar API secret nesta versão.

## Limitações

- A pesquisa de notícias e estratégias online ainda não está implementada.
- A ligação de ordens à Binance Spot Testnet ainda não está implementada.
- Forex e painel Samsung em tempo real ainda não estão implementados.
- Dados históricos podem conter lacunas; não é ferramenta validada para lucros.
- O ficheiro de estado versionado é adequado só para aprendizagem; antes de produção, migrar para base de dados externa e gestão de risco mais robusta.
