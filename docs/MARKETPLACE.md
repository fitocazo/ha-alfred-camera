# Publicação experimental no Marketplace

Esta preparação não significa aprovação no catálogo oficial. A instalação por link de repositório personalizado é distinta da inclusão no catálogo.

## Antes de tornar público

1. Conferir os resultados de protocolo, hassfest e history-secrets em Actions. Uma varredura sem achados reduz riscos, mas não garante ausência de segredos. Revisar também arquivos e histórico manualmente. Não publicar se houver credenciais.
2. Confirmar que brand/icon.png e brand/icon@2x.png estão versionados dentro de custom_components/alfred_snapshot.
3. Revisar a origem e condições de uso da marca em assets/BRAND.md. Nenhuma licença sobre a marca é concedida pelo projeto. Definir uma licença de código antes de buscar distribuição comunitária mais ampla.
4. Manter documentado: snapshots funcionando; atualização forçada e última correção de registro pendentes de validação. Não declarar versão estável.

## Configurações do GitHub (pelo proprietário)

O conector usado no desenvolvimento não oferece alteração de visibilidade ou tópicos. Na página Settings do repositório, General > Danger Zone > Change repository visibility, selecionar Public e confirmar o nome fitocazo/ha-alfred-camera. Isso expõe os arquivos e todo o histórico; cópias públicas não podem ser recolhidas com garantia. Não fazer antes da revisão acima.

Na área About, adicionar tópicos como home-assistant, custom-integration e alfredcamera. Confirmar que Issues está habilitado. Essas opções também são verificadas para o catálogo.

A validação HACS pode falhar enquanto o repositório estiver privado ou sem tópicos. Não ignorar os checks para aparentar aprovação. Após ajustar essas configurações, executar novamente o workflow Validate Marketplace preparation em Actions e conferir todos os resultados. O conector atual não executa nem lê diretamente todos os jobs do Actions.

## Adicionar no Home Assistant

No HA 2026.11+, Configurações > Marketplace > adicionar por link: https://github.com/fitocazo/ha-alfred-camera . Usar o tipo Integração se solicitado. Conectar GitHub no próprio Marketplace e aceitar pessoalmente o aviso sobre código comunitário. A conexão do assistente é separada.

A pasta da instalação manual já usa o mesmo domínio alfred_snapshot. Não excluir a entrada da conta nem editar .storage; se houver conflito de propriedade da pasta, interromper e investigar antes de sobrescrever. Guardar backup antes da primeira instalação gerenciada.

Uma atualização substitui a pasta da integração. Credenciais não devem ser guardadas nessa pasta. Código Python já carregado requer reinício do Core após atualização; não reiniciar host ou apps sem necessidade.

## Versões e limites da validação

Sem releases, a instalação usa a branch padrão. Planejar uma release experimental identificada, com tag igual à versão do manifesto, após os testes de execução. hacs.json declara HA 2026.11.0; a checagem de versão mínima do Marketplace é aplicada a releases.

Os testes de protocolo não acessam o Alfred e usam somente dados sintéticos. Eles não validam login real, renovação, config flow, ciclo de vida da entidade ou a ação de atualização forçada. Os checks remotos precisam ser executados e conferidos; não são presumidos como aprovados por terem sido adicionados.

Referências:
- https://contributors.home-assistant.io/marketplace/reference/repository-structure/
- https://contributors.home-assistant.io/marketplace/reference/validation/
- https://contributors.home-assistant.io/marketplace/guides/integrations/
