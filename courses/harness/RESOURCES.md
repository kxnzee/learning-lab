# Источники: харнесы

## Знание

### Модель харнеса
- [Anthropic: Building effective agents (дек. 2024)](https://www.anthropic.com/engineering/building-effective-agents)
  Workflows против agents, простые составные паттерны. Использовать для: когда нужен агент, а когда фиксированный сценарий в коде.
- [Addy Osmani: Agent Harness Engineering (апр. 2026)](https://addyosmani.com/blog/agent-harness-engineering/)
  «Agent = Model + Harness», состав харнеса: инструкции, инструменты, инфраструктура, оркестрация, хуки, наблюдаемость. Использовать для: схема слоёв, урок 1.
- [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)
  20 уроков от цикла `while True` до харнеса уровня Claude Code. Использовать для: устройство агентного цикла руками (разбор, не продакшен).

### Контекст и длинные сессии
- [Anthropic: Effective context engineering for AI agents (сент. 2025)](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
  Бюджет внимания, context rot, компакция, заметки, субагенты. Использовать для: почему агент «глупеет» и что с этим делать.
- [Anthropic: Effective harnesses for long-running agents (нояб. 2025)](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
  Агент-инициализатор, файл прогресса, работа по одной фиче. Использовать для: харнес для задач, не влезающих в одно окно контекста.

### Скиллы и обвязка
- [Anthropic: Equipping agents for the real world with Agent Skills (окт. 2025)](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
  Постепенное раскрытие: в контексте только имя и описание. Использовать для: как и почему срабатывают скиллы.
- [Claude Code: документация](https://code.claude.com/docs)
  Скиллы, хуки, субагенты, плагины, MCP, output styles. Использовать для: эталонная реализация слоёв.
- [Jesse Vincent: Superpowers (окт. 2025)](https://blog.fsck.com/2025/10/09/superpowers/)
  Замысел Superpowers от автора: хук старта сессии, бутстрап-скилл, обязательность скиллов. Использовать для: разбор Superpowers.
- [obra/superpowers](https://github.com/obra/superpowers)
  Исходники скиллов. У ученика вендорена v6.1.1 в `multi-repo-specs/extensions/superpowers`.
- [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code)
  ECC: агенты, скиллы, хуки, правила, кросс-харнесная поддержка. Ставить только из официальных каналов. Использовать для: разбор ECC.

### Измерение
- [Anthropic: Demystifying evals for AI agents (янв. 2026)](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
  Задачи, прогоны, грейдеры, pass@k / pass^k, старт с 20–50 задач из реальных ошибок. Использовать для: модуль evals.

### Харнесы для сравнения
- [Qwen Code](https://github.com/QwenLM/qwen-code)
  CLI-агент Qwen; доступен в банке. Использовать для: сравнение и ограничения закрытого контура.

### Свои репозитории (учебный материал, не эталон)
- [kxnzee/multi-repo-specs](https://github.com/kxnzee/multi-repo-specs) — OpenSpec Orchestrator.
- [kxnzee/sdd-openspec-process](https://github.com/kxnzee/sdd-openspec-process) — регламент SDD и план SDD Harness CLI.
- [kxnzee/specs](https://github.com/kxnzee/specs) — пилотный репозиторий спецификаций.

## Мудрость (сообщества)

- Пока не подобраны: спросить ученика, есть ли сообщества внутри банка (гильдии, чаты ИИ-трансформации) — для харнеса аналитиков они ценнее внешних.

## Пробелы

- GigaCode: не найдено публичной официальной документации по CLI и расширениям — нужна внутренняя документация банка.
- Сравнительные критерии выбора харнеса для личной работы — собрать после ответа на диагностику (вопрос 5).
