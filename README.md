# AlfredCamera Snapshots

Integracao experimental e nao oficial com Home Assistant.

Baseline 0.2.2: snapshots atualizados confirmados no HA; atualizacao forcada e ultima mudanca de registro em __init__.py ainda pendentes de validacao. Renovacao automatica experimental, sem validacao prolongada documentada. Nao e uma release estavel.

Instalacao manual: copiar custom_components/alfred_snapshot para a pasta de configuracao do HA e reiniciar o Core. Adicionar AlfredCamera Snapshots pela interface; importar somente uma sessao privada exportada localmente do WebViewer. Manter outros visualizadores dessa sessao fechados para evitar conflito de recurso.

Nao incluir credenciais, session.json, .storage, imagens, HAR, logs ou o bundle proprietario Alfred neste repositorio. As credenciais da integracao ficam no HA e podem integrar seus backups.

Esta primeira revisao preserva o codigo instalado, inclusive limitacoes conhecidas. A acao alfred_snapshot.refresh_snapshot esta implementada, mas seu registro/execucao ainda precisam ser confirmados no HA. Nao ha video ao vivo nem login independente com App Check.

Pendencias: validar registro e execucao da acao; terminar botao no dashboard; testar renovacao, reautenticacao e reinicio; adicionar testes automatizados e revisar traducoes (en.json ainda contem portugues).
