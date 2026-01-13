# 🎨 Especificações de UI - FileCopy Verifier

## 📋 Requisitos de Interface

### 🎭 Animações Fluidas e Modernas

#### Transições e Efeitos
- **Transições suaves** entre estados da aplicação
- **Animações de progresso** com efeitos visuais (pulsação, fade)
- **Efeitos de hover** em botões e elementos interativos
- **Feedback visual imediato** em todas as ações do usuário
- **Animações de entrada/saída** para elementos da interface
- **Transições de tela** ao mudar de contexto

#### Implementação Técnica
- Usar `QPropertyAnimation` para animações de propriedades
- Usar `QGraphicsEffect` para efeitos visuais (sombra, blur)
- Easing functions para movimentos naturais (ease-in-out, ease-out)
- Duração de animações: 200-400ms (rápido mas perceptível)
- Evitar animações excessivas que atrapalhem a usabilidade

---

### 📊 Seção de Arquivos em Cópia (Tempo Real)

#### Layout e Estrutura
- **Localização:** Seção dedicada abaixo da barra de progresso principal
- **Tipo:** Tabela ou Lista scrollável
- **Visibilidade:** Aparece automaticamente quando cópia inicia
- **Minimizar/Maximizar:** Botão para expandir/recolher seção

#### Informações por Arquivo
Para cada arquivo sendo copiado, exibir:

1. **Nome do arquivo**
   - Nome completo ou truncado com "..."
   - Ícone baseado no tipo de arquivo
   - Tooltip com caminho completo

2. **Barra de progresso individual**
   - Barra de progresso por arquivo
   - Porcentagem numérica (ex: "45%")
   - Cor dinâmica (azul copiando, verde concluído, vermelho erro)

3. **Tamanho do arquivo**
   - Formato: "125.5 MB" ou "2.3 GB" ou "1.2 TB"
   - Atualização em tempo real durante cópia

4. **Velocidade de cópia**
   - Formato: "15.2 MB/s"
   - Atualização a cada segundo
   - Cor baseada em velocidade (verde rápido, amarelo médio, vermelho lento)

5. **Tempo estimado restante**
   - Formato: "2m 15s" ou "45s"
   - Atualização dinâmica

6. **Status visual**
   - Ícone/indicador de status:
     - ⏳ Copiando (animado)
     - ✅ Concluído
     - ❌ Erro
     - ⏸️ Pausado

#### Funcionalidades
- **Scroll automático** para arquivo atual sendo copiado
- **Limitar exibição** a últimos N arquivos (ex: 20) para performance
- **Filtros visuais:**
  - Mostrar apenas copiando
  - Mostrar apenas concluídos
  - Mostrar apenas erros
  - Mostrar todos
- **Ordenação:**
  - Por ordem de cópia (padrão)
  - Por nome
  - Por tamanho
  - Por status

#### Atualização em Tempo Real
- Atualizar a cada 100-200ms durante cópia ativa
- Usar `QTimer` para atualizações periódicas
- Thread-safe para atualizações da UI

---

### 📈 Estatísticas de Progresso Global

#### Informações Principais
Exibir em área destacada acima da barra de progresso:

1. **Total a ser copiado**
   - Formato: "Total: 15.3 GB"
   - Formatação automática (MB/GB/TB)
   - Atualizado após escaneamento

2. **Total já copiado**
   - Formato: "Copiado: 8.7 GB"
   - Atualização em tempo real
   - Formatação automática

3. **Total restante**
   - Formato: "Restante: 6.6 GB"
   - Cálculo: Total - Copiado
   - Atualização em tempo real

4. **Barra de progresso geral**
   - Barra visual com porcentagem
   - Estilo moderno (gradiente, animação)
   - Texto de porcentagem sobreposta
   - Cor dinâmica baseada em progresso

5. **Porcentagem geral**
   - Formato: "45.2%"
   - Tamanho grande e destacado
   - Atualização suave (animação de contagem)

6. **Velocidade média global**
   - Formato: "Velocidade: 12.5 MB/s"
   - Cálculo baseado em tempo decorrido
   - Atualização a cada segundo

7. **Tempo**
   - Tempo decorrido: "Tempo: 5m 23s"
   - Tempo estimado total: "Estimado: 12m 15s"
   - Atualização contínua

8. **Contador de arquivos**
   - Formato: "Arquivos: 1,234 / 5,678"
   - Atualização em tempo real
   - Formatação com separador de milhares

#### Layout Sugerido
```
┌─────────────────────────────────────────┐
│  Total: 15.3 GB  │  Copiado: 8.7 GB    │
│  Restante: 6.6 GB │ Velocidade: 12.5 MB/s│
│  Arquivos: 1,234 / 5,678                │
│  Tempo: 5m 23s │ Estimado: 12m 15s     │
├─────────────────────────────────────────┤
│  [████████████░░░░░░░░] 45.2%          │
├─────────────────────────────────────────┤
│  Arquivos em Cópia:                     │
│  ┌───────────────────────────────────┐ │
│  │ 📄 arquivo1.txt    [████░░] 45%   │ │
│  │    125.5 MB  │ 15.2 MB/s │ 2m 15s│ │
│  ├───────────────────────────────────┤ │
│  │ ✅ arquivo2.txt    [██████] 100%  │ │
│  │    2.3 GB    │ 25.0 MB/s │ 0s    │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

### 🎨 Design Moderno

#### Estilo Visual
- **Estilo:** Flat design moderno
- **Cores:**
  - Primária: Azul moderno (#2196F3 ou similar)
  - Sucesso: Verde (#4CAF50)
  - Erro: Vermelho (#F44336)
  - Aviso: Amarelo/Laranja (#FF9800)
  - Background: Branco/Cinza claro
  - Texto: Cinza escuro (#212121)

#### Componentes
- **Botões:** Estilo flat com hover effect
- **Barras de progresso:** Gradiente suave, bordas arredondadas
- **Cards:** Sombra sutil, bordas arredondadas
- **Ícones:** Material Design ou Font Awesome
- **Tipografia:** Sans-serif moderna (Roboto, Segoe UI, etc.)

#### Responsividade
- Interface adaptável a diferentes tamanhos de janela
- Elementos reorganizam-se automaticamente
- Scroll quando necessário
- Tamanho mínimo de janela definido

---

## 🔧 Implementação Técnica

### Bibliotecas e Ferramentas
- **PyQt5/PyQt6** - Framework base
- **QPropertyAnimation** - Animações
- **QGraphicsEffect** - Efeitos visuais
- **QTimer** - Atualizações periódicas
- **QStyledItemDelegate** - Customização de células
- **QAbstractItemModel** - Modelo de dados eficiente

### Performance
- **Virtualização:** Usar QListView com modelo virtual para muitos arquivos
- **Throttling:** Limitar atualizações de UI a 5-10 FPS
- **Lazy loading:** Carregar apenas arquivos visíveis
- **Cache:** Cachear cálculos de formatação

### Thread Safety
- Todas as atualizações de UI devem ser feitas na thread principal
- Usar signals/slots para comunicação entre threads
- Evitar bloqueios da UI durante atualizações

---

## 📝 Checklist de Implementação

### Fase 2.5 - UI Moderna
- [ ] Implementar animações básicas (transições, hover)
- [ ] Criar seção de arquivos em cópia
- [ ] Implementar tabela/lista com progresso individual
- [ ] Adicionar estatísticas globais detalhadas
- [ ] Melhorar barra de progresso principal
- [ ] Implementar atualizações em tempo real
- [ ] Adicionar filtros e ordenação
- [ ] Aplicar estilo moderno (cores, tipografia, espaçamento)
- [ ] Testar performance com muitos arquivos
- [ ] Otimizar atualizações de UI

---

*Documento criado: 2024*
*Versão: 1.0*

