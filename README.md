# crptb2

Crypto Trading Bot.

実際に使用しているストラテジーはcrptb2-strategyリポジトリ(private)に格納。

## command

- Botを起動する

```bash
uv run python -m src.main
```

- Botを常時稼働にしておく

```bash
nohup uv run python -m src.main &
```

- すべてのunittestを実行する

```bash
uv run python -m unittest discover -v test
```

- 特定のunittestを実行する(例: TestIndicators)

```bash
uv run python -m unittest -v test.unit.test_indicators.TestIndicators
```
