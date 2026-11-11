# AlfredCamera Snapshots

Integração experimental e não oficial do AlfredCamera com Home Assistant.

## Estado atual

Baseline 0.2.2: snapshots atualizados confirmados no HA. A ação `alfred_snapshot.refresh_snapshot` e a última alteração de registro em `__init__.py` ainda precisam de validação. Renovação automática experimental, sem validação prolongada documentada. Não é uma release estável. Não há vídeo ao vivo nem login independente com App Check.

## Instalação manual

Copie `custom_components/alfred_snapshot` para a pasta de configuração do HA e reinicie somente o Core. Depois, adicione AlfredCamera Snapshots em Configurações > Dispositivos e serviços.

## Capturar a sessão do WebViewer

A sessão é uma credencial: quem a possui pode conseguir acessar sua conta e câmeras. Faça isso somente no seu computador e na sua conta. Não envie o resultado a chats, issues, commits ou screenshots. Desative histórico/sincronização da área de transferência se necessário.

1. Abra https://alfred.camera/webapp/viewer/ e autentique normalmente.
2. Confirme que suas câmeras aparecem.
3. No Chrome ou Edge para computador, pressione F12 ou Ctrl+Shift+I (no macOS, Command+Option+I). Selecione Console, não Network nem o terminal do sistema.
4. Confirme que o contexto do Console é a página principal do Alfred. Se houver um aviso de segurança contra colagem, leia o aviso e entenda o código antes de prosseguir; não desative proteções do navegador para executar código que você não compreende.
5. Execute o script abaixo. Ele apenas lê a sessão local e copia os campos necessários; não envia dados pela rede, não altera o armazenamento e não imprime tokens. `copy()` é um auxiliar do Console do DevTools.

```javascript
(() => {
  if (location.hostname !== "alfred.camera" ||
      !location.pathname.startsWith("/webapp/viewer")) {
    throw new Error("Execute somente no WebViewer oficial do Alfred.");
  }
  const raw = localStorage.getItem("ALFRED_WEB_VIEWER_SETTINGS");
  if (!raw) throw new Error("Sessão não encontrada neste contexto.");
  const auth = JSON.parse(raw).auth;
  const required = ["uid", "jid", "kvToken", "resource", "expireAt"];
  if (!auth || required.some(key => !auth[key])) {
    throw new Error("Sessão incompleta. Autentique novamente pelo site.");
  }
  const keys = [...required, "refreshToken", "region"];
  const session = Object.fromEntries(
    keys.filter(key => auth[key] !== undefined).map(key => [key, auth[key]])
  );
  copy(JSON.stringify(session));
  console.log("Sessão copiada. Cole somente no campo privado da integração.");
})();
```

6. Feche todas as abas WebViewer dessa sessão, sem clicar em sair da conta. Pare também o PoC Python. A integração ainda reutiliza o recurso importado: visualizadores simultâneos podem entrar em conflito.
7. Na configuração ou reautenticação da integração no HA, cole o JSON no campo privado de sessão. Não cole no código Python nem no YAML do dashboard.
8. Selecione inicialmente uma câmera. Use cache de 60 segundos e deixe a renovação automática desativada até entender e testar seu funcionamento.
9. Limpe a área de transferência após importar. Proteja o acesso ao HA e seus backups: a configuração interna contém segredos e não é um cofre criptografado.

### Problemas comuns

- Chave não encontrada: confira o site, o contexto do Console e o nome exato `ALFRED_WEB_VIEWER_SETTINGS`, com sublinhados entre WEB e VIEWER.
- Sessão incompleta ou expirada: autentique normalmente no site e exporte outra sessão. Não compartilhe tokens para diagnóstico.
- O Console mostra `undefined` após o script: isso pode ser apenas o valor de retorno; procure a mensagem de sessão copiada.
- Imagem não atualiza imediatamente: o cache limita pedidos. Confira `last_snapshot_success` e `snapshot_error`; o horário é de recebimento no HA, não um timestamp de captura fornecido pelo celular.
- Credencial exposta: remova cópias compartilhadas e use os mecanismos do serviço para encerrar/revogar sessões. Fechar uma aba ou apagar um arquivo não garante revogação no servidor.

## Ícone do Alfred no HA

O HA 2026.3+ aceita imagens locais em `custom_components/alfred_snapshot/brand/`. Usamos o símbolo e as cores do WebViewer oficial, sem sugerir que esta integração seja oficial. As marcas permanecem de seus respectivos titulares.

O SVG-fonte está em `assets/alfred-symbol.svg`. Como o conector usado para commits envia texto, um workflow gera `brand/icon.png` (256x256) e `brand/icon@2x.png` (512x512), com fundo transparente, e os grava em um commit automático separado. Ele usa `GITHUB_TOKEN` com permissão `contents: write`, sem segredos pessoais. A execução pode consumir a franquia de GitHub Actions.

Se Actions estiver desabilitado ou bloquear escrita, gere localmente, na raiz do repositório, sem instalar dependências:

```bash
python3 tools/build_brand.py
```

No Windows, use `python tools/build_brand.py`. Copie a pasta `brand` gerada junto com a integração para o HA. Apenas atualizar o GitHub não atualiza a instalação no HA. Recarregue a interface; imagens podem permanecer em cache. Uma reinicialização adicional do Core não é exigida pelo gerador de imagens.

Referência: https://contributors.home-assistant.io/core/integrations/brands/

## Segurança e pendências

Nunca versionar sessão, tokens, `.storage`, `secrets.yaml`, imagens de câmeras, HAR, logs, backups ou o bundle proprietário do Alfred. O `.gitignore` ajuda, mas não substitui revisar cada commit. Os únicos PNGs adicionados forçadamente pelo workflow são os dois ícones da marca.

Pendências: validar registro e execução da ação; terminar botão no dashboard; testar renovação, reautenticação e reinício; adicionar testes automatizados; revisar traduções (`en.json` ainda contém português).
